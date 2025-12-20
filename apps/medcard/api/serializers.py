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
