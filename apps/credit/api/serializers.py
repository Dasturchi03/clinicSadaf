from rest_framework import serializers

from apps.credit.models import Credit
from apps.client.models import Client
from apps.user.models import User


class ClientCreditSerializer(serializers.ModelSerializer):
    client_id = serializers.IntegerField(required=False)

    class Meta:
        model = Client
        fields = [
            'client_id',
            'client_firstname',
            'client_lastname'
        ]
        extra_kwargs = {
            'client_firstname': {'read_only': True},
            'client_lastname': {'read_only': True}
        }


class DoctorCreditSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = User
        fields = [
            'id',
            'user_firstname',
            'user_lastname'
        ]
        extra_kwargs = {
            'user_firstname': {'read_only': True},
            'user_lastname': {'read_only': True}
        }


class CreditSerializer(serializers.ModelSerializer):
    credit_id = serializers.IntegerField(required=False)
    credit_client = serializers.SerializerMethodField("get_credit_client")
    credit_user = serializers.SerializerMethodField("get_credit_user")

    class Meta:
        model = Credit
        fields = [
            "credit_id",
            "credit_client",
            "credit_card",
            "credit_action",
            "credit_user",
            "credit_sum",
            "credit_price",
            "credit_type",
            "credit_note",
            "credit_is_paid",
            "credit_created_at",
        ]

    def get_credit_client(self, obj):
        serializer = ClientCreditSerializer(obj.credit_client)
        return serializer.data

    def get_credit_user(self, obj):
        serializer = DoctorCreditSerializer(obj.credit_user)
        return serializer.data


class CreditUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Credit
        fields = "__all__"