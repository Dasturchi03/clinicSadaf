from datetime import datetime, timedelta

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.client.api.nested_serializer import NestedClientReservationSerializer
from apps.reservation import services
from apps.reservation.models import ReservationRequest
from apps.user.api.nested_serializers import NestedDoctorSerializer
from apps.work.api.nested_serializers import NestedWorkReservationSerializer
from apps.work.models import Work


class ReservationRequestDetailSerializer(serializers.ModelSerializer):
    client = NestedClientReservationSerializer()
    doctor = NestedDoctorSerializer()
    reservation_work = NestedWorkReservationSerializer()

    class Meta:
        model = ReservationRequest
        fields = [
            "id",
            "client",
            "doctor",
            "reservation_work",
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
    reservation_work = serializers.PrimaryKeyRelatedField(
        queryset=Work.objects.filter(deleted=False),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = ReservationRequest
        fields = [
            "id",
            "client",
            "doctor",
            "reservation_work",
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


class MobileReservationRequestSerializer(serializers.ModelSerializer):
    doctor_id = serializers.PrimaryKeyRelatedField(
        source="doctor",
        queryset=services.get_doctors_queryset(),
        write_only=True,
    )
    reservation_work_id = serializers.PrimaryKeyRelatedField(
        source="reservation_work",
        queryset=Work.objects.filter(deleted=False),
        write_only=True,
    )
    reservation_work = NestedWorkReservationSerializer(read_only=True)
    doctor = NestedDoctorSerializer(read_only=True)
    date = serializers.DateField(format="%d-%m-%Y", input_formats=["%d-%m-%Y"])
    time = serializers.TimeField(format="%H:%M", input_formats=["%H:%M"])
    slot_minutes = serializers.IntegerField(write_only=True, required=False, default=60)

    class Meta:
        model = ReservationRequest
        fields = [
            "id",
            "flutter_reservation_id",
            "doctor_id",
            "doctor",
            "reservation_work_id",
            "reservation_work",
            "doctor_name",
            "status",
            "note",
            "date",
            "time",
            "slot_minutes",
        ]
        extra_kwargs = {
            "doctor_name": {"read_only": True},
            "status": {"read_only": True},
        }

    def validate(self, attrs):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise ValidationError("Authentication required")
        if not getattr(request.user, "client_user", None):
            raise ValidationError("Current user is not linked to a client")

        doctor = attrs["doctor"]
        reservation_work = attrs["reservation_work"]
        target_date = attrs["date"]
        start_time = attrs["time"]
        slot_minutes = services.normalize_slot_minutes(attrs.get("slot_minutes"))
        end_time = (
            datetime.combine(target_date, start_time) + timedelta(minutes=slot_minutes)
        ).time()
        services.ensure_reservation_available(
            doctor=doctor,
            target_date=target_date,
            start_time=start_time,
            end_time=end_time,
        )
        doctor_specialization_ids = set(
            doctor.user_specialization.values_list("specialization_id", flat=True)
        )
        work_specialization_ids = set(
            reservation_work.specialization.values_list("specialization_id", flat=True)
        )
        if work_specialization_ids and not (
            doctor_specialization_ids & work_specialization_ids
        ):
            raise ValidationError(
                {"reservation_work_id": "Selected service does not belong to this doctor"}
            )
        attrs["slot_minutes"] = slot_minutes
        return attrs

    def create(self, validated_data):
        validated_data.pop("slot_minutes", None)
        request = self.context["request"]
        validated_data["client"] = request.user.client_user
        validated_data["doctor_name"] = validated_data["doctor"].full_name()
        return super().create(validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["status"] = instance.get_status_display()
        return data
