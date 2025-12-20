from rest_framework import serializers

from apps.client.models import Client


class NestedClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ["client_id", "client_firstname", "client_lastname"]


class NestedClientReservationSerializer(serializers.ModelSerializer):
    # used in reservation serializers

    public_phone = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = (
            "client_id",
            "client_firstname",
            "client_lastname",
            "client_birthdate",
            "public_phone",
        )

    def get_public_phone(self, instance):
        public_phone = instance.client_public_phone.all()
        try:
            return public_phone[:1][0].public_phone
        except:
            return ""
