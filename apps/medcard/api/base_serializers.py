import datetime
from datetime import date

from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.client.api.serializers import PatientSerializer
from apps.client.models import Client, Client_Public_Phone
from apps.core.choices import TransactionTypes
from apps.credit.models import Credit
from apps.disease.models import Disease
from apps.expenses.constants import (
    INCOME_TYPE_TITLE_PAY_MEDICAL_CARD,
    INCOME_TYPE_TITLES,
)
from apps.expenses.models import FinancialReport, IncomeType
from apps.medcard.models import Action, MedicalCard, Stage, Tooth
from apps.report.models import MedicalCardReport
from apps.transaction.models import Transaction
from apps.user.api.nested_serializers import NestedDoctorSerializer
from apps.user.api.serializers import DoctorSerializer
from apps.user.models import User, UserSalary
from apps.work.models import Work


class WorkMedCardSerializer(serializers.ModelSerializer):
    work_id = serializers.IntegerField(required=False)

    class Meta:
        model = Work
        fields = ["work_id", "work_title"]
        extra_kwargs = {"work_title": {"read_only": True}}


class DiseaseMedCardSerializer(serializers.ModelSerializer):
    disease_id = serializers.IntegerField(required=False)

    class Meta:
        model = Disease
        fields = ["disease_id", "parent", "disease_title"]
        extra_kwargs = {
            "disease_title": {"read_only": True},
            "parent": {"read_only": True},
        }


class BaseActionSerializer(serializers.ModelSerializer):
    action_work = WorkMedCardSerializer()
    action_doctor = DoctorSerializer(required=False, allow_null=True)
    action_disease = DiseaseMedCardSerializer(required=False)
    action_created_by = NestedDoctorSerializer(read_only=True)

    class Meta:
        model = Action
        fields = [
            "action_id",
            "action_work",
            "action_doctor",
            "action_created_by",
            "action_disease",
            "action_quantity",
            "action_price",
            "action_price_type",
            "action_note",
            "transaction_action",
            "credit_action",
            "action_finished_at",
            "action_is_done",
            "action_is_paid",
            "action_is_cancelled",
        ]


class BaseStageSerializer(serializers.ModelSerializer):
    stage_created_by = NestedDoctorSerializer(read_only=True)

    class Meta:
        model = Stage
        fields = [
            "stage_id",
            "tooth",
            "action_stage",
            "stage_created_by",
            "stage_is_done",
            "stage_is_paid",
            "stage_is_cancelled",
            "stage_index",
        ]


class BaseMedicalCardSerializer(serializers.ModelSerializer):
    client = PatientSerializer()

    class Meta:
        model = MedicalCard
        fields = [
            "card_id",
            "client",
            "card_price",
            "card_discount_price",
            "card_discount_percent",
            "card_is_done",
            "card_is_paid",
            "card_is_cancelled",
            "card_finished_at",
            "stage",
        ]
        read_only_fields = [
            "client",
            "card_price",
            "card_discount_price",
            "card_discount_percent",
            "card_finished_at",
            "card_is_done",
            "card_is_paid",
            "card_is_cancelled",
        ]

    def create(self, validated_data):
        current_user = self.context.get("current_user")
        client_data = validated_data.pop("client")
        actions_list = []

        try:
            client_id = client_data.pop("client_id")
            client_instance = Client.objects.get(pk=client_id)
            client_phone = Client_Public_Phone.objects.filter(
                client=client_instance
            ).first()

        except Client.DoesNotExist:
            raise ValidationError(f"Client with id: {client_id} does not exists")

        medical_card = MedicalCard(client_id=client_id)
        medical_card.save()

        stage_data = validated_data.pop("stage")

        for stages in stage_data:
            tooth_data = stages.pop("tooth", None)

            if tooth_data:
                tooth_id = tooth_data.pop("tooth_id")
                stage_instance = Stage.objects.create(
                    tooth_id=tooth_id,
                    card=medical_card,
                    stage_created_by=current_user,
                    stage_index=0,
                )
            else:
                stage_instance = Stage.objects.create(
                    card=medical_card, stage_created_by=current_user, stage_index=0
                )

            action_data = stages.pop("action_stage")
            for actions in action_data:
                work_data = actions.pop("action_work")
                work_id = work_data.pop("work_id")

                doctor_data = actions.pop("action_doctor", None)
                if doctor_data:
                    doctor_id = doctor_data.pop("id")
                else:
                    doctor_id = None

                disease_data = actions.pop("action_disease", None)
                if disease_data:
                    disease_id = disease_data.pop("disease_id")
                else:
                    disease_id = None

                action_instance = Action.objects.create(
                    action_stage=stage_instance,
                    action_work_id=work_id,
                    action_doctor_id=doctor_id,
                    action_disease_id=disease_id,
                    action_created_by=current_user,
                    action_note=actions["action_note"],
                    action_price=actions["action_price"],
                    action_price_type=actions["action_price_type"],
                    action_quantity=actions["action_quantity"],
                    action_is_done=actions["action_is_done"],
                )
                medical_card_report = MedicalCardReport.objects.create(
                    client=client_instance,
                    client_name=client_instance.full_name(),
                    client_phone=client_phone.public_phone if client_phone else None,
                    doctor=action_instance.action_doctor,
                    doctor_name=(
                        action_instance.action_doctor.full_name()
                        if action_instance.action_doctor
                        else None
                    ),
                    action=action_instance,
                )
                actions_list.append(action_instance)

                if action_instance.action_is_done:
                    action_instance.action_finished_at = datetime.datetime.now()
                    action_instance.action_is_paid = True
                    action_instance.save()

                    client_instance = Client.objects.get(client_id=client_id)
                    client_instance.client_balance -= action_instance.action_price
                    client_instance.save(update_fields=["client_balance"])

                    transaction = Transaction.objects.create(
                        transaction_type=TransactionTypes.PAY_FOR_ACTION,
                        transaction_client=client_instance,
                        transaction_user=current_user,
                        transaction_card=medical_card,
                        transaction_action=action_instance,
                        transaction_sum=action_instance.action_price,
                        transaction_action_price=action_instance.action_price,
                    )
                    income_type_title = INCOME_TYPE_TITLES[
                        INCOME_TYPE_TITLE_PAY_MEDICAL_CARD
                    ]

                    # fetch related financial report related income type
                    income_type, _ = IncomeType.objects.get_or_create(
                        title=income_type_title, defaults={"title": income_type_title}
                    )
                    financial_report = FinancialReport.objects.create(
                        report_income_type=income_type,
                        report_title=action_instance.action_work.work_title,
                        report_created_by=current_user,
                        report_for_user=action_instance.action_doctor,
                        report_card=medical_card,
                        report_action=action_instance,
                        report_work=action_instance.action_work,
                        report_action_price=action_instance.action_price,
                        report_work_price=action_instance.action_work.work_basic_price,
                        report_sum=transaction.transaction_sum,
                        report_quantity=action_instance.action_quantity,
                    )
                    medical_card_report.transactions.add(transaction)
                    medical_card_report.financial_reports.add(financial_report)

                    if action_instance.action_doctor is not None:
                        self.create_salary_for_doctor(
                            card_instance=medical_card,
                            client_instance=client_instance,
                            action_instance=action_instance,
                            action_doctor=action_instance.action_doctor,
                            action_work=action_instance.action_work,
                            medical_card_report=medical_card_report,
                        )
                    else:
                        raise ValidationError(
                            "Please provide doctor information for this action"
                        )

        actions_sum = sum(action.action_price for action in actions_list)
        medical_card.card_price = actions_sum
        medical_card.save(update_fields=["card_price"])
        return medical_card

    def update(self, instance, validated_data):
        current_user = self.context.get("current_user")
        client_instance = instance.client

        stages_data = validated_data.pop("stage", None)
        client_data = validated_data.pop("client", None)

        for key, value in validated_data.items():
            setattr(instance, key, value)

        if instance.card_is_done:
            instance.card_finished_at = datetime.datetime.now()

        client_id = client_data.get("client_id") if client_data else None
        instance.client_id = client_id

        if stages_data:
            for stage_data in stages_data:
                stage_id = stage_data.pop("stage_id", None)

                if stage_id is not None:
                    stage_instance = Stage.objects.get(pk=stage_id)

                    if stage_instance.stage_is_cancelled:
                        raise ValidationError("You cannot change cancelled stage")

                    if stage_data.get("deleted") is True:
                        self.validate_stage_before_delete(
                            stage_instance=stage_instance, current_user=current_user
                        )

                    else:
                        actions_data = stage_data.pop("action_stage", None)

                        if actions_data:
                            for action_data in actions_data:
                                action_id = action_data.pop("action_id", None)

                                if action_id is not None:
                                    action_instance = Action.objects.get(pk=action_id)
                                    medical_card_report = (
                                        MedicalCardReport.objects.filter(
                                            action=action_instance
                                        ).first()
                                    )

                                    if action_data.get("deleted") is True:
                                        self.validate_action_before_delete(
                                            stage_instance=stage_instance,
                                            action_instance=action_instance,
                                            current_user=current_user,
                                        )

                                    else:
                                        doctor_data = action_data.pop(
                                            "action_doctor", None
                                        )
                                        work_data = action_data.pop("action_work", None)
                                        disease_data = action_data.pop(
                                            "action_disease", None
                                        )
                                        credit_data = action_data.pop(
                                            "credit_action", None
                                        )
                                        transaction_data = action_data.pop(
                                            "transaction_action", None
                                        )
                                        action_is_cancelled = action_data.pop(
                                            "action_is_cancelled", False
                                        )

                                        for key, value in action_data.items():
                                            setattr(action_instance, key, value)

                                        doctor_instance = (
                                            User.objects.get(pk=doctor_data.pop("id"))
                                            if doctor_data
                                            else None
                                        )
                                        work_instance = (
                                            Work.objects.get(
                                                pk=work_data.pop("work_id")
                                            )
                                            if work_data
                                            else None
                                        )
                                        disease_instance = (
                                            Disease.objects.get(
                                                pk=disease_data.pop("disease_id")
                                            )
                                            if disease_data
                                            else None
                                        )

                                        action_instance.action_doctor = doctor_instance
                                        action_instance.action_work = work_instance
                                        action_instance.action_disease = (
                                            disease_instance
                                        )

                                        original_action = Action.objects.filter(
                                            action_id=action_instance.pk
                                        ).first()
                                        if (
                                            not original_action.action_is_done
                                            and not original_action.action_is_paid
                                            and action_instance.action_is_done
                                        ):

                                            transactions = Transaction.objects.filter(
                                                Q(
                                                    transaction_type=TransactionTypes.PAY_FOR_ACTION
                                                )
                                                | Q(
                                                    transaction_type=TransactionTypes.PARTIALLY_PAY_FOR_ACTION
                                                ),
                                                transaction_action=action_instance,
                                            )

                                            _credits = Credit.objects.filter(
                                                credit_action=action_instance
                                            )

                                            if (
                                                not transactions.exists()
                                                and not _credits.exists()
                                            ):
                                                action_instance.action_is_paid = True
                                                client_instance.client_balance -= (
                                                    action_instance.action_price
                                                )
                                                client_instance.save(
                                                    update_fields=["client_balance"]
                                                )

                                                transaction = Transaction.objects.create(
                                                    transaction_type=TransactionTypes.PAY_FOR_ACTION,
                                                    transaction_client=client_instance,
                                                    transaction_card=instance,
                                                    transaction_user=current_user,
                                                    transaction_action=action_instance,
                                                    transaction_sum=action_instance.action_price,
                                                    transaction_action_price=action_instance.action_price,
                                                )
                                                income_type_title = INCOME_TYPE_TITLES[
                                                    INCOME_TYPE_TITLE_PAY_MEDICAL_CARD
                                                ]

                                                # fetch related financial report related income type
                                                income_type, _ = (
                                                    IncomeType.objects.get_or_create(
                                                        title=income_type_title,
                                                        defaults={
                                                            "title": income_type_title
                                                        },
                                                    )
                                                )
                                                financial_report = FinancialReport.objects.create(
                                                    report_income_type=income_type,
                                                    report_title=action_instance.action_work.work_title,
                                                    report_created_by=current_user,
                                                    report_for_user=action_instance.action_doctor,
                                                    report_card=instance,
                                                    report_action=action_instance,
                                                    report_work=action_instance.action_work,
                                                    report_action_price=action_instance.action_price,
                                                    report_work_price=action_instance.action_work.work_basic_price,
                                                    report_sum=transaction.transaction_sum,
                                                    report_quantity=action_instance.action_quantity,
                                                )
                                                if medical_card_report:
                                                    medical_card_report.transactions.add(
                                                        transaction
                                                    )
                                                    medical_card_report.financial_reports.add(
                                                        financial_report
                                                    )

                                        if action_instance.action_is_done:
                                            if not action_instance.action_finished_at:
                                                action_instance.action_finished_at = (
                                                    datetime.datetime.now()
                                                )
                                            if (
                                                action_instance.action_doctor
                                                is not None
                                            ):
                                                self.create_salary_for_doctor(
                                                    card_instance=instance,
                                                    client_instance=client_instance,
                                                    action_instance=action_instance,
                                                    action_doctor=action_instance.action_doctor,
                                                    action_work=action_instance.action_work,
                                                    medical_card_report=medical_card_report,
                                                )
                                            else:
                                                raise ValidationError(
                                                    "Please provide doctor information for this action"
                                                )

                                        can_update_action = (
                                            action_instance.action_doctor
                                            or action_instance.action_created_by
                                            or stage_instance.stage_created_by
                                        ) == current_user

                                        if stage_instance.stage_index != 0:
                                            if (
                                                can_update_action
                                                and not action_instance.action_is_cancelled
                                            ):
                                                action_instance.save()
                                        else:
                                            if can_update_action:
                                                action_instance.save(
                                                    update_fields=[
                                                        "action_doctor",
                                                        "action_note",
                                                        "action_is_done",
                                                        "action_is_paid",
                                                        "action_finished_at",
                                                    ]
                                                )

                                        if current_user.has_perm(
                                            "medcard.change_medicalcard_admin"
                                        ):
                                            if not action_instance.action_is_cancelled:
                                                action_instance.save()

                                        if current_user.has_perm(
                                            "medcard.change_medicalcard_admin"
                                        ) or current_user.has_perm(
                                            "medcard.change_medicalcard_cashier"
                                        ):
                                            if (
                                                action_instance.action_is_done
                                                or action_instance.action_is_paid
                                            ):
                                                action_instance.action_is_cancelled = (
                                                    action_is_cancelled
                                                )
                                                action_instance.save()

                                        if current_user.has_perm(
                                            "medcard.change_medicalcard_cashier"
                                        ):
                                            self.create_credit_and_transaction(
                                                card_instance=instance,
                                                credit_data=credit_data,
                                                transaction_data=transaction_data,
                                                action_instance=action_instance,
                                                client_instance=client_instance,
                                                current_user=current_user,
                                                medical_card_report=medical_card_report,
                                            )
                                else:

                                    self.create_action(
                                        card_instance=stage_instance.card,
                                        action_data=action_data,
                                        stage_instance=stage_instance,
                                        client_instance=client_instance,
                                        current_user=current_user,
                                    )

                        stage_instance.stage_is_cancelled = stage_data.get(
                            "stage_is_cancelled", stage_instance.stage_is_cancelled
                        )

                        paid_actions = Action.objects.filter(
                            ~Q(action_is_paid=True), action_stage_id=stage_instance.pk
                        )
                        done_actions = Action.objects.filter(
                            ~Q(action_is_done=True), action_stage_id=stage_instance.pk
                        )

                        if not paid_actions.exists():
                            stage_instance.stage_is_paid = True
                        else:
                            stage_instance.stage_is_paid = False

                        if not done_actions.exists():
                            stage_instance.stage_is_done = True
                        else:
                            stage_instance.stage_is_done = False

                        stage_instance.save()
                else:
                    self.create_stage(
                        card_instance=instance,
                        stage_data=stage_data,
                        current_user=current_user,
                    )

        paid_stages = Stage.objects.filter(~Q(stage_is_paid=True), card_id=instance.pk)
        done_stages = Stage.objects.filter(~Q(stage_is_done=True), card_id=instance.pk)

        if not paid_stages.exists():
            instance.card_is_paid = True
        else:
            instance.card_is_paid = False

        if not done_stages.exists():
            instance.card_is_done = True
        else:
            instance.card_is_done = False

        stage_query = Stage.objects.select_related("card").filter(card_id=instance.pk)
        action_query = Action.objects.filter(action_stage__in=stage_query)
        actions_sum = sum(action.action_price for action in action_query)

        instance.card_price = actions_sum if actions_sum else 0
        instance.save()

        instance.refresh_from_db()
        return instance

    def validate_stage_before_delete(self, stage_instance, current_user):
        paid_or_done_actions = Action.objects.filter(
            Q(action_stage_id=stage_instance.pk, action_is_done=True)
            | Q(action_stage_id=stage_instance.pk, action_is_paid=True)
        )
        if paid_or_done_actions.exists():
            msg = "You cannot delete a stage that has paid or done actions."
            raise ValidationError(msg)
        else:
            Action.objects.filter(action_stage_id=stage_instance.pk).delete()
            stage_instance.delete()

    def validate_action_before_delete(
        self, stage_instance, action_instance, current_user
    ):
        if (
            action_instance.action_is_done
            or action_instance.action_is_paid
            or action_instance.action_is_cancelled
        ):
            raise ValidationError("You have no access to delete this action")

        Credit.objects.filter(credit_action=action_instance).delete()
        action_instance.delete()

    def create_salary_for_doctor(
        self,
        card_instance,
        client_instance,
        action_instance,
        action_doctor,
        action_work,
        medical_card_report,
    ):
        if UserSalary.objects.filter(
            salary_for_user=action_doctor, salary_action=action_instance
        ).exists():
            pass

        else:
            salary_instance = UserSalary(
                salary_for_user=action_doctor,
                salary_action=action_instance,
                salary_card=card_instance,
                salary_work=action_work,
                salary_work_type=action_work.work_salary_type,
                salary_action_price=action_instance.action_price,
                salary_work_price=action_work.work_basic_price,
                salary_is_paid=False,
            )

            if salary_instance.salary_work_type == "Fixed":
                salary_instance.salary_amount = (
                    action_work.work_fixed_salary_amount
                    * action_instance.action_quantity
                )

            elif salary_instance.salary_work_type == "Percent":

                if action_doctor.user_salary_child_percent != 0:

                    current_date = date.today()
                    client_age = (
                        current_date - client_instance.client_birthdate
                    ).days // 365.25

                    if client_age < 12:
                        salary_instance.salary_amount = (
                            (action_doctor.user_salary_child_percent / 100)
                            * action_instance.action_price
                            * action_instance.action_quantity
                        )

                    if client_age >= 12:
                        salary_instance.salary_amount = (
                            (action_doctor.user_salary_percent / 100)
                            * action_instance.action_price
                            * action_instance.action_quantity
                        )

                else:
                    salary_instance.salary_amount = (
                        (action_doctor.user_salary_percent / 100)
                        * action_instance.action_price
                        * action_instance.action_quantity
                    )

            elif salary_instance.salary_work_type == "Hybrid":
                salary_instance.salary_amount = (
                    action_work.work_hybrid_salary_amount
                    / 2
                    * action_instance.action_quantity
                )

            salary_instance.save()
            if medical_card_report:
                medical_card_report.salaries.add(salary_instance)

    def create_credit_and_transaction(
        self,
        card_instance,
        credit_data,
        transaction_data,
        action_instance,
        client_instance,
        current_user,
        medical_card_report,
    ):
        if credit_data:
            for credit in credit_data:
                if not credit.get("credit_id"):
                    credit_instance = Credit.objects.create(
                        credit_client=client_instance,
                        credit_card=card_instance,
                        credit_action=action_instance,
                        credit_user=current_user,
                        credit_sum=action_instance.action_price,
                        credit_price=action_instance.action_price,
                        credit_type=credit.get("credit_type"),
                        credit_note=credit.get("credit_note"),
                    )

                    if credit_instance.credit_type == "Vip":
                        transaction_instance = Transaction.objects.create(
                            transaction_type=TransactionTypes.VIP_CREDIT,
                            transaction_client=client_instance,
                            transaction_user=current_user,
                            transaction_card=card_instance,
                            transaction_action=action_instance,
                            transaction_credit=credit_instance,
                            transaction_sum=action_instance.action_price,
                            transaction_action_price=action_instance.action_price,
                            transaction_work_basic_price=action_instance.action_work.work_basic_price,
                            transaction_work_vip_price=action_instance.action_work.work_vip_price,
                            transaction_work_discount_price=action_instance.action_work.work_discount_price,
                            transaction_work_discount_percent=action_instance.action_work.work_discount_percent,
                            transaction_loss=action_instance.action_price,
                        )

                    if medical_card_report:
                        medical_card_report.credits.add(credit_instance)
                        if credit_instance.credit_type == "Vip":
                            medical_card_report.transactions.add(transaction_instance)

        if transaction_data:
            for transaction in transaction_data:
                if not transaction.get("transaction_id"):
                    transaction_instance = Transaction.objects.create(
                        transaction_type=transaction.get("transaction_type"),
                        transaction_client=client_instance,
                        transaction_user=current_user,
                        transaction_card=card_instance,
                        transaction_action=action_instance,
                        transaction_sum=transaction.get("transaction_sum"),
                        transaction_action_price=action_instance.action_price,
                        transaction_discount_price=transaction.get(
                            "transaction_discount_price", 0
                        ),
                        transaction_discount_percent=transaction.get(
                            "transaction_discount_percent", 0
                        ),
                        transaction_work_basic_price=action_instance.action_work.work_basic_price,
                        transaction_work_vip_price=action_instance.action_work.work_vip_price,
                        transaction_work_discount_price=action_instance.action_work.work_discount_price,
                        transaction_work_discount_percent=action_instance.action_work.work_discount_percent,
                        transaction_benefit=transaction.get("transaction_sum"),
                    )

                    if transaction_instance.transaction_discount_price != 0:
                        transaction_instance.transaction_sum = (
                            action_instance.action_price
                            - transaction_instance.transaction_discount_price
                        )
                    if transaction_instance.transaction_discount_percent != 0:
                        transaction_instance.transaction_sum = (
                            1
                            - (transaction_instance.transaction_discount_percent / 100)
                        ) * action_instance.action_price

                    if (
                        client_instance.client_balance
                        >= transaction_instance.transaction_sum
                    ):
                        client_instance.client_balance -= (
                            transaction_instance.transaction_sum
                        )
                        client_instance.save(update_fields=["client_balance"])
                        income_type_title = INCOME_TYPE_TITLES[
                            INCOME_TYPE_TITLE_PAY_MEDICAL_CARD
                        ]

                        # fetch related financial report related income type
                        income_type, _ = IncomeType.objects.get_or_create(
                            title=income_type_title,
                            defaults={"title": income_type_title},
                        )
                        financial_report = FinancialReport.objects.create(
                            report_income_type=income_type,
                            report_title=action_instance.action_work.work_title,
                            report_created_by=current_user,
                            report_for_user=action_instance.action_doctor,
                            report_card=card_instance,
                            report_action=action_instance,
                            report_work=action_instance.action_work,
                            report_action_price=action_instance.action_price,
                            report_work_price=action_instance.action_work.work_basic_price,
                            report_sum=transaction_instance.transaction_sum,
                            report_quantity=action_instance.action_quantity,
                        )
                    else:
                        raise ValidationError(
                            f"Client balance is not enough for this action: {action_instance} ({action_instance.action_price})"
                        )

                    if medical_card_report:
                        medical_card_report.transactions.add(transaction_instance)
                        medical_card_report.financial_reports.add(financial_report)

                    if (
                        transaction_instance.transaction_sum
                        < action_instance.action_price
                    ):
                        action_price_remainder = (
                            action_instance.action_price
                            - transaction_instance.transaction_sum
                        )

                        credit_instance = Credit.objects.create(
                            credit_client=client_instance,
                            credit_card=card_instance,
                            credit_action=action_instance,
                            credit_user=current_user,
                            credit_sum=action_price_remainder,
                            credit_price=action_price_remainder,
                            credit_type="Basic",
                        )

                        if medical_card_report:
                            medical_card_report.credits.add(credit_instance)

                    if (
                        transaction_instance.transaction_sum
                        == action_instance.action_price
                    ):
                        action_instance.action_is_paid = True
                        action_instance.save(update_fields=["action_is_paid"])

    def create_action(
        self, card_instance, action_data, stage_instance, client_instance, current_user
    ):

        work_data = action_data.pop("action_work", None)
        work_id = work_data.pop("work_id") if work_data else None

        disease_data = action_data.pop("action_disease", None)
        disease_id = disease_data.get("disease_id") if disease_data else None

        doctor_data = action_data.pop("action_doctor", None)
        doctor_id = doctor_data.get("id") if doctor_data else None

        client_phone = Client_Public_Phone.objects.filter(
            client=client_instance
        ).first()

        action_instance = Action.objects.create(
            action_stage=stage_instance,
            action_work_id=work_id,
            action_doctor_id=doctor_id,
            action_disease_id=disease_id,
            action_created_by=current_user,
            **action_data,
        )
        medical_card_report = MedicalCardReport.objects.create(
            client=client_instance,
            client_name=client_instance.full_name(),
            client_phone=client_phone.public_phone if client_phone else None,
            doctor=action_instance.action_doctor,
            doctor_name=(
                action_instance.action_doctor.full_name()
                if action_instance.action_doctor
                else None
            ),
            action=action_instance,
        )
        if action_instance.action_is_done:
            action_instance.action_is_paid = True
            action_instance.action_finished_at = datetime.datetime.now()
            action_instance.save(update_fields=["action_is_paid", "action_finished_at"])

            client_instance.client_balance -= action_instance.action_price
            client_instance.save(update_fields=["client_balance"])

            transaction = Transaction.objects.create(
                transaction_type=TransactionTypes.PAY_FOR_ACTION,
                transaction_client=client_instance,
                transaction_user=current_user,
                transaction_card=card_instance,
                transaction_action=action_instance,
                transaction_sum=action_instance.action_price,
                transaction_action_price=action_instance.action_price,
            )
            income_type_title = INCOME_TYPE_TITLES[INCOME_TYPE_TITLE_PAY_MEDICAL_CARD]

            # fetch related financial report related income type
            income_type, _ = IncomeType.objects.get_or_create(
                title=income_type_title, defaults={"title": income_type_title}
            )
            financial_report = FinancialReport.objects.create(
                report_income_type=income_type,
                report_title=action_instance.action_work.work_title,
                report_created_by=current_user,
                report_for_user=action_instance.action_doctor,
                report_card=card_instance,
                report_action=action_instance,
                report_work=action_instance.action_work,
                report_action_price=action_instance.action_price,
                report_work_price=action_instance.action_work.work_basic_price,
                report_sum=transaction.transaction_sum,
                report_quantity=action_instance.action_quantity,
            )
            if medical_card_report:
                medical_card_report.transactions.add(transaction)
                medical_card_report.financial_reports.add(financial_report)

        credit_data = action_data.pop("credit_action", None)
        transaction_data = action_data.pop("transaction_action", None)

        self.create_credit_and_transaction(
            card_instance=card_instance,
            credit_data=credit_data,
            transaction_data=transaction_data,
            action_instance=action_instance,
            client_instance=client_instance,
            current_user=current_user,
            medical_card_report=medical_card_report,
        )

        if action_instance.action_is_done and action_instance.action_doctor:
            self.create_salary_for_doctor(
                card_instance=card_instance,
                client_instance=client_instance,
                action_instance=action_instance,
                action_doctor=action_instance.action_doctor,
                action_work=action_instance.action_work,
                medical_card_report=medical_card_report,
            )

    def create_stage(self, card_instance, stage_data, current_user):
        latest_stage_instance = Stage.objects.filter(card_id=card_instance.pk).latest(
            "stage_id"
        )
        tooth_data = stage_data.pop("tooth", None)

        if tooth_data:
            tooth_instance = Tooth.objects.get(pk=tooth_data.pop("tooth_id"))

            stage_instance = Stage(
                tooth=tooth_instance,
                card=card_instance,
                stage_created_by=current_user,
                stage_index=latest_stage_instance.stage_index + 1,
            )

        else:
            stage_instance = Stage(
                card=card_instance,
                stage_created_by=current_user,
                stage_index=latest_stage_instance.stage_index + 1,
            )

        stage_instance.save()

        actions_data = stage_data.pop("action_stage")

        for action_data in actions_data:

            self.create_action(
                card_instance=card_instance,
                action_data=action_data,
                stage_instance=stage_instance,
                client_instance=card_instance.client,
                current_user=current_user,
            )
