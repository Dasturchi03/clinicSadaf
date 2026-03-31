from django.db.models import Sum
from rest_framework import serializers

from apps.client.api.nested_serializer import NestedClientSerializer
from apps.credit.api.serializers import CreditSerializer
from apps.medcard.api.base_serializers import (
    BaseActionSerializer,
    BaseMedicalCardSerializer,
    BaseStageSerializer,
)
from apps.medcard.api.nested_serializers import NestedToothSerializer
from apps.medcard.models import Action, MedicalCard, Stage, Tooth, Xray
from apps.reservation.models import Reservation
from apps.transaction.api.serializers import TransactionSerializer
from apps.user.api.nested_serializers import NestedDoctorSerializer
from apps.user.models import User


class ToothSerializer(serializers.ModelSerializer):
    tooth_id = serializers.IntegerField(required=False)
    tooth_image = serializers.ImageField(use_url=False, required=False, read_only=True)

    class Meta:
        model = Tooth
        fields = ["tooth_id", "tooth_type", "tooth_number", "tooth_image"]
        extra_kwargs = {
            "tooth_type": {"read_only": True},
            "tooth_number": {"read_only": True},
        }


class ActionCreateSerializer(BaseActionSerializer):
    transaction_action = TransactionSerializer(read_only=True, many=True)
    credit_action = CreditSerializer(read_only=True, many=True)

    class Meta(BaseActionSerializer.Meta):
        read_only_fields = [
            "action_is_paid",
            "action_is_cancelled",
            "action_finished_at",
        ]


class ActionUpdateSerializer(BaseActionSerializer):
    action_id = serializers.IntegerField(required=False)
    transaction_action = TransactionSerializer(
        required=False, allow_null=True, many=True
    )
    credit_action = CreditSerializer(required=False, allow_null=True, many=True)

    class Meta(BaseActionSerializer.Meta):
        model = Action
        fields = BaseActionSerializer.Meta.fields + ["deleted"]
        read_only_fields = ["action_finished_at"]


class StageCreateSerializer(BaseStageSerializer):
    tooth = ToothSerializer(required=False)
    action_stage = ActionCreateSerializer(many=True)

    class Meta(BaseStageSerializer.Meta):
        read_only_fields = [
            "stage_index",
            "stage_is_done",
            "stage_is_paid",
            "stage_is_cancelled",
        ]


class StageUpdateSerializer(BaseStageSerializer):
    stage_id = serializers.IntegerField(required=False)
    tooth = ToothSerializer(required=False)
    action_stage = ActionUpdateSerializer(many=True, required=False)

    class Meta(BaseStageSerializer.Meta):
        model = Stage
        fields = BaseStageSerializer.Meta.fields + ["deleted"]
        read_only_fields = ["stage_index", "stage_is_done", "stage_is_paid"]


class MedicalCardCreateSerializer(BaseMedicalCardSerializer):
    stage = StageCreateSerializer(many=True)

    class Meta(BaseMedicalCardSerializer.Meta):
        pass


class MedicalCardUpdateSerializer(BaseMedicalCardSerializer):
    stage = StageUpdateSerializer(many=True, required=False)

    class Meta(BaseMedicalCardSerializer.Meta):
        pass


class MedicalCardListSerializer(serializers.ModelSerializer):
    card_doctors = serializers.SerializerMethodField("get_card_doctors")

    class Meta:
        model = MedicalCard
        fields = [
            "card_id",
            "card_is_done",
            "card_doctors",
            "card_created_at",
            "card_finished_at",
        ]
        extra_kwargs = {
            "card_id": {"read_only": True},
            "card_finished_at": {"read_only": True},
            "client": {"read_only": True},
            "card_is_done": {"read_only": True},
        }

    def get_card_doctors(self, instance):
        doctors = (
            User.objects.filter(action_doctor__action_stage__card=instance)
            .only("id", "user_firstname", "user_lastname")
            .distinct()
        )
        serializer = NestedDoctorSerializer(doctors, many=True)
        return serializer.data


class ActionViewSetUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = "__all__"


class XraySerializer(serializers.ModelSerializer):
    class Meta:
        model = Xray
        fields = ["id", "client", "medical_card", "stage", "tooth", "image"]


class XrayDetailSerializer(serializers.ModelSerializer):
    client = NestedClientSerializer()
    tooth = NestedToothSerializer()

    class Meta:
        model = Xray
        fields = ["id", "client", "medical_card", "stage", "tooth", "image"]


class XrayBulkUploadSerializer(serializers.ModelSerializer):
    images = serializers.ListField(child=serializers.ImageField(), write_only=True)

    class Meta:
        model = Xray
        fields = ["client", "medical_card", "stage", "tooth", "images"]


class MobileTreatmentActionSerializer(serializers.ModelSerializer):
    action_work_title = serializers.SerializerMethodField()
    doctor = NestedDoctorSerializer(source="action_doctor", read_only=True)

    class Meta:
        model = Action
        fields = [
            "action_id",
            "action_work_title",
            "doctor",
            "action_note",
            "action_price",
            "action_is_done",
            "action_is_paid",
            "action_finished_at",
        ]

    def get_action_work_title(self, obj):
        return obj.action_work.work_title if obj.action_work else None


class MobileTreatmentStageSerializer(serializers.ModelSerializer):
    tooth = NestedToothSerializer(read_only=True)
    action_stage = MobileTreatmentActionSerializer(many=True, read_only=True)

    class Meta:
        model = Stage
        fields = [
            "stage_id",
            "stage_index",
            "stage_is_done",
            "stage_is_paid",
            "tooth",
            "action_stage",
        ]


class MobileTreatmentPlanItemSerializer(serializers.Serializer):
    action_id = serializers.IntegerField()
    stage_id = serializers.IntegerField(allow_null=True)
    stage_index = serializers.IntegerField(allow_null=True)
    tooth_number = serializers.CharField(allow_null=True)
    service_title = serializers.CharField(allow_null=True)
    doctor_name = serializers.CharField(allow_null=True)
    reservation_date = serializers.CharField(allow_null=True)
    reservation_start_time = serializers.CharField(allow_null=True)
    reservation_end_time = serializers.CharField(allow_null=True)
    estimated_duration_days = serializers.IntegerField(allow_null=True)
    estimated_duration_label = serializers.CharField(allow_null=True)
    price = serializers.FloatField()
    is_done = serializers.BooleanField()
    is_paid = serializers.BooleanField()


class MobileTreatmentListSerializer(serializers.ModelSerializer):
    doctors = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    paid_amount = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()
    reservation_request_id = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    payment_status_label = serializers.SerializerMethodField()
    card_number = serializers.SerializerMethodField()
    reservation_summary = serializers.SerializerMethodField()
    reservation_datetime = serializers.SerializerMethodField()
    treatment_plan_summary = serializers.SerializerMethodField()
    treatment_plan_count = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = MedicalCard
        fields = [
            "card_id",
            "card_number",
            "card_price",
            "card_discount_price",
            "card_discount_percent",
            "card_is_done",
            "card_is_paid",
            "card_finished_at",
            "doctors",
            "doctor_name",
            "paid_amount",
            "remaining_amount",
            "total_price",
            "reservation_request_id",
            "status",
            "status_label",
            "payment_status",
            "payment_status_label",
            "reservation_summary",
            "reservation_datetime",
            "treatment_plan_summary",
            "treatment_plan_count",
            "card_created_at",
        ]

    def _get_card_actions(self, obj):
        prefetched_stages = getattr(obj, "_prefetched_objects_cache", {}).get("stage")
        if prefetched_stages is not None:
            actions = []
            for stage in prefetched_stages:
                stage_actions = getattr(stage, "_prefetched_objects_cache", {}).get(
                    "action_stage"
                )
                if stage_actions is not None:
                    actions.extend(stage_actions)
                else:
                    actions.extend(stage.action_stage.all())
            return actions
        return list(
            Action.objects.filter(action_stage__card=obj)
            .select_related("action_doctor", "action_work", "action_date", "action_stage__tooth")
            .order_by("action_stage__stage_index", "action_id")
        )

    def _get_latest_reservation(self, obj):
        actions = [action for action in self._get_card_actions(obj) if action.action_date_id]
        if not actions:
            return None
        actions.sort(
            key=lambda action: (
                action.action_date.reservation_date,
                action.action_date.reservation_start_time,
                action.action_date_id,
            ),
            reverse=True,
        )
        return actions[0].action_date

    def _build_plan_titles(self, obj):
        titles = []
        seen = set()
        for action in self._get_card_actions(obj):
            title = action.action_work.work_title if action.action_work else None
            if not title or title in seen:
                continue
            seen.add(title)
            titles.append(title)
        return titles

    def get_doctors(self, obj):
        doctors = (
            User.objects.filter(action_doctor__action_stage__card=obj)
            .only("id", "user_firstname", "user_lastname")
            .distinct()
        )
        return NestedDoctorSerializer(doctors, many=True).data

    def get_doctor_name(self, obj):
        doctors = self.get_doctors(obj)
        if not doctors:
            return None
        first_doctor = doctors[0]
        return " ".join(
            filter(None, [first_doctor.get("user_firstname"), first_doctor.get("user_lastname")])
        ) or None

    def get_paid_amount(self, obj):
        paid_amount = obj.transaction_card.aggregate(total=Sum("transaction_sum"))["total"]
        return paid_amount or 0

    def get_remaining_amount(self, obj):
        total_price = obj.card_discount_price or obj.card_price or 0
        paid_amount = self.get_paid_amount(obj)
        return max(total_price - paid_amount, 0)

    def get_status(self, obj):
        if obj.card_is_done:
            return "completed"
        if any(action.action_is_done for action in self._get_card_actions(obj)):
            return "in_progress"
        if self._get_latest_reservation(obj):
            return "accepted"
        return "in_progress"

    def get_reservation_request_id(self, obj):
        reservation = self._get_latest_reservation(obj)
        if not reservation:
            return None
        reservation_request = getattr(reservation, "reservation_request", None)
        return reservation_request.pk if reservation_request else None

    def get_payment_status(self, obj):
        if obj.card_is_paid:
            return "paid"
        paid_amount = self.get_paid_amount(obj)
        if paid_amount > 0:
            return "partial"
        return "unpaid"

    def get_status_label(self, obj):
        mapping = {
            "accepted": "Qabul",
            "in_progress": "Jarayonda",
            "completed": "O'tilgan",
        }
        return mapping.get(self.get_status(obj), "Jarayonda")

    def get_payment_status_label(self, obj):
        mapping = {
            "paid": "To'langan",
            "partial": "Qisman to'langan",
            "unpaid": "To'lanmagan",
        }
        return mapping.get(self.get_payment_status(obj), "To'lanmagan")

    def get_card_number(self, obj):
        return f"N {obj.card_id}"

    def get_reservation_summary(self, obj):
        reservation = self._get_latest_reservation(obj)
        if not reservation:
            return None
        reservation_request = getattr(reservation, "reservation_request", None)
        return {
            "reservation_id": reservation.reservation_id,
            "reservation_request_id": reservation_request.pk if reservation_request else None,
            "date": reservation.reservation_date.strftime("%d-%m-%Y"),
            "start_time": reservation.reservation_start_time.strftime("%H:%M"),
            "end_time": reservation.reservation_end_time.strftime("%H:%M"),
            "doctor_name": reservation.reservation_doctor.full_name()
            if reservation.reservation_doctor
            else None,
            "service_title": reservation.reservation_work.work_title
            if reservation.reservation_work
            else None,
            "is_initial": reservation.is_initial,
        }

    def get_reservation_datetime(self, obj):
        reservation = self.get_reservation_summary(obj)
        if not reservation:
            return None
        return f'{reservation["date"]}, {reservation["start_time"]} - {reservation["end_time"]}'

    def get_treatment_plan_summary(self, obj):
        titles = self._build_plan_titles(obj)
        if not titles:
            return None
        if len(titles) <= 3:
            return ", ".join(titles)
        return ", ".join(titles[:3]) + f" +{len(titles) - 3}"

    def get_treatment_plan_count(self, obj):
        return len(self._build_plan_titles(obj))

    def get_total_price(self, obj):
        return obj.card_discount_price or obj.card_price or 0


class MobileTreatmentDetailSerializer(MobileTreatmentListSerializer):
    client = NestedClientSerializer(read_only=True)
    stage = MobileTreatmentStageSerializer(many=True, read_only=True)
    credits = serializers.SerializerMethodField()
    transactions = TransactionSerializer(source="transaction_card", many=True, read_only=True)
    treatment_plan = serializers.SerializerMethodField()
    card_title = serializers.SerializerMethodField()
    contract_link = serializers.SerializerMethodField()

    class Meta(MobileTreatmentListSerializer.Meta):
        fields = MobileTreatmentListSerializer.Meta.fields + [
            "client",
            "stage",
            "credits",
            "transactions",
            "treatment_plan",
            "card_title",
            "contract_link",
        ]

    def get_credits(self, obj):
        credits = obj.credit_card.all().order_by("-credit_created_at")
        return CreditSerializer(credits, many=True).data

    def get_treatment_plan(self, obj):
        items = []
        for action in self._get_card_actions(obj):
            reservation = action.action_date
            items.append(
                {
                    "action_id": action.action_id,
                    "stage_id": action.action_stage_id,
                    "stage_index": action.action_stage.stage_index
                    if action.action_stage
                    else None,
                    "tooth_number": action.action_stage.tooth.tooth_number
                    if action.action_stage and action.action_stage.tooth
                    else None,
                    "service_title": action.action_work.work_title
                    if action.action_work
                    else None,
                    "doctor_name": action.action_doctor.full_name()
                    if action.action_doctor
                    else None,
                    "reservation_date": reservation.reservation_date.strftime("%d-%m-%Y")
                    if reservation
                    else None,
                    "reservation_start_time": reservation.reservation_start_time.strftime("%H:%M")
                    if reservation
                    else None,
                    "reservation_end_time": reservation.reservation_end_time.strftime("%H:%M")
                    if reservation
                    else None,
                    "estimated_duration_days": action.action_work.estimated_duration_days
                    if action.action_work
                    else None,
                    "estimated_duration_label": self._format_duration_label(
                        action.action_work.estimated_duration_days
                    )
                    if action.action_work
                    else None,
                    "price": action.action_price or 0,
                    "is_done": action.action_is_done,
                    "is_paid": action.action_is_paid,
                }
            )
        return MobileTreatmentPlanItemSerializer(items, many=True).data

    def _format_duration_label(self, duration_days):
        if not duration_days:
            return None
        if duration_days % 7 == 0:
            weeks = duration_days // 7
            return f"{weeks} hafta"
        return f"{duration_days} kun"

    def get_card_title(self, obj):
        return f"Davolanish kartasi {self.get_card_number(obj)}"

    def get_contract_link(self, obj):
        return None
