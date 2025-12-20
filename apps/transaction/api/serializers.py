from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.client.api.serializers import PatientSerializer
from apps.core.choices import TransactionTypes
from apps.credit.models import Credit
from apps.expenses.constants import (
    EXPENSE_TYPE_TITLE_REFUND,
    EXPENSE_TYPE_TITLES,
    FINANCIAL_REPORT_TITLE_REFUND,
    FINANCIAL_REPORT_TITLES,
    INCOME_TYPE_TITLE,
    INCOME_TYPE_TITLE_PAY_CREDIT,
    INCOME_TYPE_TITLE_PAY_MEDICAL_CARD,
    INCOME_TYPE_TITLES,
)
from apps.expenses.models import ExpensesType, FinancialReport, IncomeType
from apps.medcard.models import Action, MedicalCard, Stage
from apps.report.models import MedicalCardReport
from apps.transaction.models import Transaction
from apps.user.api.nested_serializers import NestedDoctorSerializer


class TransactionSerializer(serializers.ModelSerializer):
    transaction_id = serializers.UUIDField(required=False)
    transaction_client = PatientSerializer(read_only=True)
    transaction_user = NestedDoctorSerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "transaction_id",
            "transaction_type",
            "transaction_payment_type",
            "transaction_client",
            "transaction_user",
            "transaction_card",
            "transaction_action",
            "transaction_credit",
            "transaction_sum",
            "transaction_action_price",
            "transaction_discount_price",
            "transaction_discount_percent",
            "transaction_work_basic_price",
            "transaction_work_vip_price",
            "transaction_work_discount_price",
            "transaction_work_discount_percent",
            "transaction_card_discount_price",
            "transaction_card_discount_percent",
            "transaction_benefit",
            "transaction_loss",
            "transaction_created_at",
            "transaction_updated_at",
            "comment",
        ]
        extra_kwargs = {
            "transaction_card": {"read_only": True},
            "transaction_client": {"read_only": True},
            "transaction_user": {"read_only": True},
            "transaction_action": {"read_only": True},
            "transaction_credit": {"read_only": True},
            "transaction_action_price": {"read_only": True},
            "transaction_work_basic_price": {"read_only": True},
            "transaction_work_vip_price": {"read_only": True},
            "transaction_work_discount_price": {"read_only": True},
            "transaction_work_discount_percent": {"read_only": True},
            "transaction_card_discount_price": {"read_only": True},
            "transaction_card_discount_percent": {"read_only": True},
            "transaction_benefit": {"read_only": True},
            "transaction_loss": {"read_only": True},
            "transaction_created_at": {"read_only": True},
            "transaction_updated_at": {"read_only": True},
            "comment": {"read_only": True},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["transaction_type"] = instance.get_transaction_type_display()
        data["transaction_payment_type"] = (
            instance.get_transaction_payment_type_display()
        )
        return data


class TransactionClientBalanceSerializer(serializers.ModelSerializer):
    # used to refill client balance

    class Meta:
        model = Transaction
        fields = [
            "transaction_id",
            "transaction_client",
            "transaction_sum",
            "transaction_payment_type",
            "comment",
        ]

    def create(self, validated_data):
        current_user = self.context.get("current_user")
        client_instance = validated_data.get("transaction_client")
        transaction_sum = validated_data.get("transaction_sum")
        transaction_payment_type = validated_data.get("transaction_payment_type")
        comment = validated_data.get("comment")
        report_income_type_title = INCOME_TYPE_TITLES[INCOME_TYPE_TITLE]

        # fetch related financial report related income type
        report_income_type, created = IncomeType.objects.get_or_create(
            title=report_income_type_title, defaults={"title": report_income_type_title}
        )

        # create financial report
        financial_report = FinancialReport.objects.create(
            report_income_type=report_income_type,
            report_title=transaction_payment_type,
            report_for_client=client_instance,
            report_created_by=current_user,
            report_sum=transaction_sum,
        )

        # create related transaction
        transaction = Transaction.objects.create(
            financial_report=financial_report,
            transaction_type=TransactionTypes.REFILL_CLIENT_BALANCE,
            transaction_client=client_instance,
            transaction_user=current_user,
            transaction_sum=transaction_sum,
            transaction_payment_type=transaction_payment_type,
            comment=comment
        )

        # update client balance
        client_instance.client_balance += transaction_sum
        client_instance.save(update_fields=["client_balance"])
        return transaction


class TransactionClientBalanceUpdateSerializer(serializers.ModelSerializer):
    # used to update transaction that used to refill client balance

    class Meta:
        model = Transaction
        fields = ["transaction_sum", "transaction_payment_type"]

    def update(self, instance, validated_data):
        # as we update transaction which refills balance, we should return transaction sum before update
        client_balance = instance.transaction_client.client_balance
        client_balance -= instance.transaction_sum

        # update transaction
        validated_data["updated_by"] = self.context["current_user"]
        instance = super().update(instance, validated_data)

        # update related financial report
        instance.financial_report.report_sum = instance.transaction_sum
        instance.financial_report.report_title = instance.transaction_payment_type
        instance.financial_report.save(update_fields=["report_sum", "report_title"])

        # set new balance value
        instance.transaction_client.client_balance = (
            client_balance + instance.transaction_sum
        )
        instance.transaction_client.save(update_fields=["client_balance"])
        return instance


class TransactionClientRefundSerializer(serializers.ModelSerializer):
    # used to refund client balance

    class Meta:
        model = Transaction
        fields = [
            "transaction_client",
            "transaction_sum",
        ]

    def create(self, validated_data):
        current_user = self.context.get("current_user")
        client_instance = validated_data.get("transaction_client")
        transaction_sum = validated_data.get("transaction_sum")
        report_expense_type_title = EXPENSE_TYPE_TITLES[EXPENSE_TYPE_TITLE_REFUND]

        # ensure client has enough balance
        if client_instance.client_balance < transaction_sum:
            raise ValidationError(
                _(f"Client with id: {client_instance.pk} does not have enough balance")
            )

        # fetch related financial report related expense type
        report_expense_type, created = ExpensesType.objects.get_or_create(
            expenses_type_title=report_expense_type_title,
            defaults={"expenses_type_title": report_expense_type_title},
        )
        # create financial report
        financial_report = FinancialReport.objects.create(
            report_expense_type=report_expense_type,
            report_title=FINANCIAL_REPORT_TITLES[FINANCIAL_REPORT_TITLE_REFUND],
            report_for_client=client_instance,
            report_created_by=current_user,
            report_sum=transaction_sum,
        )

        # create related transaction
        transaction = Transaction.objects.create(
            financial_report=financial_report,
            transaction_type=TransactionTypes.REFUND_CLIENT_BALANCE,
            transaction_client=client_instance,
            transaction_user=current_user,
            transaction_sum=transaction_sum,
        )

        # update client balance
        client_instance.client_balance -= transaction.transaction_sum
        client_instance.save(update_fields=["client_balance"])
        return transaction


class TransferClientBalanceSerializer(serializers.ModelSerializer):
    # used to transfer balance from one client to another

    class Meta:
        model = Transaction
        fields = ["transaction_sum", "transaction_client", "transaction_receiver"]

    def create(self, validated_data):
        current_user = self.context.get("current_user")
        client_instance = validated_data.get("transaction_client")
        receiver_instance = validated_data.get("transaction_receiver")

        # ensure client has enough balance
        if client_instance.client_balance < validated_data.get("transaction_sum"):
            raise ValidationError(
                _(f"Client with id: {client_instance.pk} does not have enough balance")
            )

        # create transaction
        transaction = Transaction.objects.create(
            transaction_client=client_instance,
            transaction_receiver=receiver_instance,
            transaction_user=current_user,
            transaction_sum=validated_data.get("transaction_sum"),
        )

        # update client balance
        client_instance.client_balance -= transaction.transaction_sum
        client_instance.save(update_fields=["client_balance"])

        # update receiver client balance
        receiver_instance.client_balance += transaction.transaction_sum
        receiver_instance.save(update_fields=["client_balance"])
        return transaction


class TransactionCreditSerializer(serializers.ModelSerializer):
    # used as child serializer
    class Meta:
        model = Transaction
        fields = [
            "transaction_credit",
            "transaction_sum",
        ]


class TransactionCreditPaySerializer(serializers.ModelSerializer):
    """Serializer for creating transactions for array of credits"""

    transaction_credits = serializers.ListSerializer(
        child=TransactionCreditSerializer(), write_only=True
    )

    class Meta:
        model = Transaction
        fields = ["transaction_client", "transaction_credits"]

    def create(self, validated_data):
        current_user = self.context.get("current_user")
        client_instance = validated_data.get("transaction_client")
        transaction_credits_data = validated_data.pop("transaction_credits")
        report_income_type_title = INCOME_TYPE_TITLES[INCOME_TYPE_TITLE_PAY_CREDIT]
        _credits = []

        for credits_data in transaction_credits_data:
            credit_instance = credits_data.get("transaction_credit")
            transaction_sum = credits_data.get("transaction_sum")
            action_instance = credit_instance.credit_action
            medical_card_report = MedicalCardReport.objects.filter(
                action=action_instance
            ).first()

            if credit_instance.credit_is_paid:
                raise ValidationError(_("Credit is already paid"))

            if transaction_sum > client_instance.client_balance:
                raise ValidationError(
                    _(
                        f"Client with id: {client_instance.pk} does not have enough balance"
                    )
                )

            if credit_instance.credit_price < transaction_sum:
                raise ValidationError(
                    _(
                        f"Maximum transaction sum for this credit is {credit_instance.credit_price}"
                    )
                )

            # fetch related financial report related income type
            report_income_type, created = IncomeType.objects.get_or_create(
                title=report_income_type_title,
                defaults={"title": report_income_type_title},
            )

            transaction = Transaction(
                transaction_type=TransactionTypes.PARTIALLY_PAY_CREDIT,
                transaction_client=client_instance,
                transaction_user=current_user,
                transaction_card=credit_instance.credit_card,
                transaction_action=action_instance,
                transaction_credit=credit_instance,
                transaction_sum=transaction_sum,
                transaction_action_price=action_instance.action_price,
                transaction_work_basic_price=action_instance.action_work.work_basic_price,
                transaction_work_vip_price=action_instance.action_work.work_vip_price,
                transaction_work_discount_price=action_instance.action_work.work_discount_price,
                transaction_work_discount_percent=action_instance.action_work.work_discount_percent,
                transaction_benefit=transaction_sum,
            )

            client_instance.client_balance -= transaction_sum
            credit_instance.credit_sum -= transaction_sum

            financial_report = FinancialReport(
                report_income_type=report_income_type,
                report_title=action_instance.action_work.work_title,
                report_created_by=current_user,
                report_for_client=client_instance,
                report_for_user=action_instance.action_doctor,
                report_card=credit_instance.credit_card,
                report_action=action_instance,
                report_work=action_instance.action_work,
                report_action_price=action_instance.action_price,
                report_work_price=action_instance.action_work.work_basic_price,
                report_sum=transaction.transaction_sum,
            )

            if credit_instance.credit_sum <= 0:
                credit_instance.credit_is_paid = True
                transaction.transaction_type = TransactionTypes.PAID_CREDIT

            transaction.save()
            financial_report.save()
            _credits.append(credit_instance)

            if medical_card_report:
                medical_card_report.transactions.add(transaction)
                medical_card_report.financial_reports.add(financial_report)

        Credit.objects.bulk_update(_credits, fields=["credit_sum", "credit_is_paid"])
        client_instance.save(update_fields=["client_balance"])

        action_credits = Action.objects.filter(
            pk=credit_instance.credit_action.action_id, action_is_paid=False
        )
        if action_credits.exists():
            unpaid_credits = Credit.objects.filter(
                credit_action__in=action_credits, credit_is_paid=False
            )
            if not unpaid_credits.exists():
                credit_instance.credit_action.action_is_paid = True
                credit_instance.credit_action.save()
        return validated_data


class TransactionCreditPayAllSerializer(serializers.ModelSerializer):
    """Serializer fully repaying all clients credits"""

    class Meta:
        model = Transaction
        fields = ["transaction_client"]

    def create(self, validated_data):
        current_user = self.context.get("current_user")
        client_instance = validated_data.get("transaction_client")
        report_income_type_title = INCOME_TYPE_TITLES[INCOME_TYPE_TITLE_PAY_CREDIT]

        # fetch related unpaid credits
        credits_queryset = Credit.objects.filter(
            credit_client_id=client_instance
        ).exclude(credit_is_paid=True)

        # ensure that client has unpaid credits
        if not credits_queryset.exists():
            raise ValidationError(
                _(f"Client with id: {client_instance.pk} does not have unpaid credits")
            )

        # ensure that client has enough balance
        credits_sum = credits_queryset.aggregate(Sum("credit_sum"))
        if client_instance.client_balance < credits_sum.get("credit_sum__sum"):
            raise ValidationError(
                _(f"Client with id: {client_instance.pk} does not have enough balance")
            )

        # fetch related financial report related income type
        report_income_type, created = IncomeType.objects.get_or_create(
            title=report_income_type_title, defaults={"title": report_income_type_title}
        )

        # process pay for credits
        for credit_instance in credits_queryset:
            action_instance = credit_instance.credit_action
            medical_card_report = MedicalCardReport.objects.filter(
                action=action_instance
            ).first()

            transaction = Transaction.objects.create(
                transaction_type=TransactionTypes.PAID_CREDIT,
                transaction_client=client_instance,
                transaction_user=current_user,
                transaction_card=credit_instance.credit_card,
                transaction_action=action_instance,
                transaction_credit_id=credit_instance.credit_id,
                transaction_sum=credit_instance.credit_sum,
                transaction_action_price=action_instance.action_price,
                transaction_work_basic_price=action_instance.action_work.work_basic_price,
                transaction_work_vip_price=action_instance.action_work.work_vip_price,
                transaction_work_discount_price=action_instance.action_work.work_discount_price,
                transaction_work_discount_percent=action_instance.action_work.work_discount_percent,
                transaction_benefit=credit_instance.credit_sum,
            )

            financial_report = FinancialReport(
                report_income_type=report_income_type,
                report_title=action_instance.action_work.work_title,
                report_created_by=current_user,
                report_for_client=client_instance,
                report_for_user=action_instance.action_doctor,
                report_card=credit_instance.credit_card,
                report_action=action_instance,
                report_work=action_instance.action_work,
                report_action_price=action_instance.action_price,
                report_work_price=action_instance.action_work.work_basic_price,
                report_sum=transaction.transaction_sum,
            )
            client_instance.client_balance -= credit_instance.credit_sum

            if medical_card_report:
                medical_card_report.transactions.add(transaction)
                medical_card_report.financial_reports.add(financial_report)

        credits_queryset.update(credit_is_paid=True, credit_sum=0)
        client_instance.save()
        return validated_data


class TransactionMedicalCardSerializer(serializers.ModelSerializer):
    """Serializer for creating transactions for all actions of a medical card"""

    transaction_card_discount_price = serializers.FloatField(
        required=False, allow_null=True
    )
    transaction_card_discount_percent = serializers.IntegerField(
        required=False, allow_null=True
    )

    class Meta:
        model = Transaction
        fields = [
            "transaction_card",
            "transaction_card_discount_price",
            "transaction_card_discount_percent",
        ]

    def create(self, validated_data):
        current_user = self.context.get("current_user")
        report_income_type_title = INCOME_TYPE_TITLES[
            INCOME_TYPE_TITLE_PAY_MEDICAL_CARD
        ]

        if not current_user.has_perm("medcard.change_medicalcard_cashier"):
            raise ValidationError(_("Permission denied!"))

        transaction_card_discount_price = validated_data.get(
            "transaction_card_discount_price", None
        )
        transaction_card_discount_percent = validated_data.get(
            "transaction_card_discount_percent", None
        )

        medical_card_instance = validated_data.get("transaction_card")
        client_instance = medical_card_instance.client
        stage_query = Stage.objects.filter(
            card_id=medical_card_instance, stage_is_paid=False
        )
        action_query = Action.objects.filter(
            action_stage__in=stage_query, action_is_paid=False
        )

        if not stage_query.exists():
            raise ValidationError(_("Medical card is already paid"))

        if not action_query.exists():
            raise ValidationError(_("Medical card is already paid"))

        credit_query = Credit.objects.filter(
            credit_action__in=action_query, credit_is_paid=False
        )
        if credit_query.exists():
            raise ValidationError("Sorry you have unpaid credits")

        # fetch related financial report related income type
        report_income_type, created = IncomeType.objects.get_or_create(
            title=report_income_type_title, defaults={"title": report_income_type_title}
        )

        # Calculate total original amount (action_price already includes quantity)
        total_original_amount = sum(action.action_price for action in action_query)

        # Calculate discount amounts based on type
        if transaction_card_discount_price:
            # Fixed amount discount - ensure it doesn't exceed total
            total_discount_amount = min(
                transaction_card_discount_price, total_original_amount
            )

            for action_instance in action_query:
                # Calculate this action's proportion of total cost
                action_proportion = action_instance.action_price / total_original_amount

                # Calculate discount for this action (proportional)
                action_discount = total_discount_amount * action_proportion

                # Final amount for this action
                action_final_amount = action_instance.action_price - action_discount

                medical_card_report = MedicalCardReport.objects.filter(
                    action=action_instance
                ).first()

                transaction_instance = Transaction(
                    transaction_type=TransactionTypes.PAY_FOR_ACTION,
                    transaction_client=client_instance,
                    transaction_user=current_user,
                    transaction_card=medical_card_instance,
                    transaction_action=action_instance,
                    transaction_action_price=action_instance.action_price,
                    transaction_work_basic_price=action_instance.action_work.work_basic_price,
                    transaction_work_vip_price=action_instance.action_work.work_vip_price,
                    transaction_work_discount_price=action_instance.action_work.work_discount_price,
                    transaction_work_discount_percent=action_instance.action_work.work_discount_percent,
                    transaction_sum=action_final_amount,
                    transaction_benefit=action_final_amount,
                    transaction_card_discount_price=transaction_card_discount_price,
                )

                # Update client balance
                client_instance.client_balance -= action_final_amount

                financial_report = FinancialReport(
                    report_income_type=report_income_type,
                    report_title=action_instance.action_work.work_title,
                    report_created_by=current_user,
                    report_for_client=client_instance,
                    report_for_user=action_instance.action_doctor,
                    report_card=medical_card_instance,
                    report_action=action_instance,
                    report_work=action_instance.action_work,
                    report_action_price=action_instance.action_price,
                    report_work_price=action_instance.action_work.work_basic_price,
                    report_sum=action_final_amount,
                )

                transaction_instance.save()
                financial_report.save()

                if medical_card_report:
                    medical_card_report.transactions.add(transaction_instance)
                    medical_card_report.financial_reports.add(financial_report)

        if transaction_card_discount_percent:
            # Percentage discount
            discount_multiplier = (100 - transaction_card_discount_percent) / 100

            for action_instance in action_query:
                action_final_amount = action_instance.action_price * discount_multiplier

                medical_card_report = MedicalCardReport.objects.filter(
                    action=action_instance
                ).first()

                transaction_instance = Transaction(
                    transaction_type=TransactionTypes.PAY_FOR_ACTION,
                    transaction_client=client_instance,
                    transaction_user=current_user,
                    transaction_card=medical_card_instance,
                    transaction_action=action_instance,
                    transaction_action_price=action_instance.action_price,
                    transaction_work_basic_price=action_instance.action_work.work_basic_price,
                    transaction_work_vip_price=action_instance.action_work.work_vip_price,
                    transaction_work_discount_price=action_instance.action_work.work_discount_price,
                    transaction_work_discount_percent=action_instance.action_work.work_discount_percent,
                    transaction_sum=action_final_amount,
                    transaction_benefit=action_final_amount,
                    transaction_card_discount_percent=transaction_card_discount_percent,
                )

                # Update client balance
                client_instance.client_balance -= action_final_amount

                financial_report = FinancialReport(
                    report_income_type=report_income_type,
                    report_title=action_instance.action_work.work_title,
                    report_created_by=current_user,
                    report_for_client=client_instance,
                    report_for_user=action_instance.action_doctor,
                    report_card=medical_card_instance,
                    report_action=action_instance,
                    report_work=action_instance.action_work,
                    report_action_price=action_instance.action_price,
                    report_work_price=action_instance.action_work.work_basic_price,
                    report_sum=action_final_amount,
                )

                transaction_instance.save()
                financial_report.save()

                if medical_card_report:
                    medical_card_report.transactions.add(transaction_instance)
                    medical_card_report.financial_reports.add(financial_report)

        # Calculate total card price and apply discounts
        if transaction_card_discount_price:
            total_card_price = total_original_amount - min(
                transaction_card_discount_price, total_original_amount
            )
        elif transaction_card_discount_percent:
            discount_multiplier = (100 - transaction_card_discount_percent) / 100
            total_card_price = total_original_amount * discount_multiplier
        else:
            total_card_price = total_original_amount

        # Update medical card with discount information, payment status, and total price
        update_fields = {"card_is_paid": True, "card_price": total_card_price}
        if transaction_card_discount_price:
            update_fields["card_discount_price"] = transaction_card_discount_price
        if transaction_card_discount_percent:
            update_fields["card_discount_percent"] = transaction_card_discount_percent

        MedicalCard.objects.filter(pk=medical_card_instance.pk).update(**update_fields)

        # Mark all actions as paid
        action_query.update(action_is_paid=True)
        stage_query.update(stage_is_paid=True)

        # Save client balance changes
        client_instance.save()

        return validated_data


class TransactionMedicalCardCreditSerializer(serializers.ModelSerializer):
    """Serializer for creating credits for all actions of a medical card"""

    transaction_card = serializers.IntegerField(required=True)
    credit_type = serializers.CharField(max_length=30, write_only=True)

    class Meta:
        model = Transaction
        fields = ["transaction_card", "credit_type"]

    def create(self, validated_data):
        current_user = self.context.get("current_user")
        if current_user.has_perm("medcard.change_medicalcard_cashier"):
            raise ValidationError(_("Permission denied!"))

        medical_card_instance = MedicalCard.objects.get(
            pk=validated_data.get("transaction_card")
        )
        stage_query = Stage.objects.filter(
            card_id=medical_card_instance, stage_is_paid=False
        )
        action_query = Action.objects.filter(
            action_stage__in=stage_query, action_is_paid=False
        )
        credit_query = Credit.objects.filter(
            credit_action__in=action_query, credit_is_paid=False
        )

        if not stage_query.exists():
            raise ValidationError(_("Medical card is already paid"))

        if not action_query.exists():
            raise ValidationError(_("Medical card is already paid"))

        if not credit_query.exists():
            raise ValidationError(_("Medical card is already credited"))

        for action_instance in action_query:
            medical_card_report = MedicalCardReport.objects.filter(
                action=action_instance
            ).first()

            credit_instance = Credit.objects.create(
                credit_client=medical_card_instance.client,
                credit_card=medical_card_instance,
                credit_action=action_instance,
                credit_user=current_user,
                credit_sum=action_instance.action_price,
                credit_price=action_instance.action_price,
                credit_type=validated_data.get("credit_type"),
            )
            if medical_card_report:
                medical_card_report.credits.add(credit_instance)
        return validated_data


class TransactionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"
