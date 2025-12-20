from rest_framework import serializers

from apps.client.api.nested_serializer import NestedClientReservationSerializer
from apps.reservation.models import ReservationRequest
from apps.user.api.nested_serializers import NestedDoctorSerializer


class ReservationRequestDetailSerializer(serializers.ModelSerializer):
    client = NestedClientReservationSerializer()
    doctor = NestedDoctorSerializer()

    class Meta:
        model = ReservationRequest
        fields = [
            "id",
            "client",
            "doctor",
            "doctor_name",
            "reservation",
            "status",
            "note",
            "date",
            "time",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["status"] = instance.get_status_display()
        return data


class ReservationRequestSerializer(serializers.ModelSerializer):
    date = serializers.DateField(format="%d-%m-%Y", input_formats=["%d-%m-%Y"])
    time = serializers.TimeField(format="%H:%M", input_formats=["%H:%M"])

    class Meta:
        model = ReservationRequest
        fields = [
            "id",
            "client",
            "doctor",
            "doctor_name",
            "reservation",
            "flutter_reservation_id",
            "status",
            "note",
            "date",
            "time",
        ]
        extra_kwargs = {
            "reservation": {"read_only": True},
            "doctor_name": {"read_only": True},
        }

    def create(self, validated_data):
        validated_data["doctor_name"] = validated_data["doctor"].full_name()
        return super().create(validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["status"] = instance.get_status_display()
        return data


class ReservationRequestApproveSerializer(serializers.Serializer):
    end_time = serializers.TimeField(format="%H:%M", input_formats=["%H:%M"])
    is_initial = serializers.BooleanField(default=False)
