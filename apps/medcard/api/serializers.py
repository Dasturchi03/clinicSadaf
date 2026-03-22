from rest_framework import serializers
from django.db.models import Sum

from apps.client.api.nested_serializer import NestedClientSerializer
from apps.credit.api.serializers import CreditSerializer
from apps.medcard.api.base_serializers import (
    BaseActionSerializer,
    BaseMedicalCardSerializer,
    BaseStageSerializer,
)
from apps.medcard.api.nested_serializers import NestedToothSerializer
from apps.medcard.models import Action, MedicalCard, Stage, Tooth, Xray
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


class MobileTreatmentListSerializer(serializers.ModelSerializer):
    doctors = serializers.SerializerMethodField()
    paid_amount = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = MedicalCard
        fields = [
            "card_id",
            "card_price",
            "card_discount_price",
            "card_discount_percent",
            "card_is_done",
            "card_is_paid",
            "card_finished_at",
            "doctors",
            "paid_amount",
            "remaining_amount",
            "status",
            "card_created_at",
        ]

    def get_doctors(self, obj):
        doctors = (
            User.objects.filter(action_doctor__action_stage__card=obj)
            .only("id", "user_firstname", "user_lastname")
            .distinct()
        )
        return NestedDoctorSerializer(doctors, many=True).data

    def get_paid_amount(self, obj):
        paid_amount = obj.transaction_card.aggregate(total=Sum("transaction_sum"))["total"]
        return paid_amount or 0

    def get_remaining_amount(self, obj):
        total_price = obj.card_discount_price or obj.card_price or 0
        paid_amount = self.get_paid_amount(obj)
        return max(total_price - paid_amount, 0)

    def get_status(self, obj):
        if obj.card_is_paid:
            return "paid"
        if obj.card_is_done:
            return "in_progress"
        return "active"


class MobileTreatmentDetailSerializer(MobileTreatmentListSerializer):
    client = NestedClientSerializer(read_only=True)
    stage = MobileTreatmentStageSerializer(many=True, read_only=True)
    credits = serializers.SerializerMethodField()
    transactions = TransactionSerializer(source="transaction_card", many=True, read_only=True)

    class Meta(MobileTreatmentListSerializer.Meta):
        fields = MobileTreatmentListSerializer.Meta.fields + [
            "client",
            "stage",
            "credits",
            "transactions",
        ]

    def get_credits(self, obj):
        credits = obj.credit_card.all().order_by("-credit_created_at")
        return CreditSerializer(credits, many=True).data
