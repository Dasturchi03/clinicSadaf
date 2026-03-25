from datetime import datetime, timedelta

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.client.api.nested_serializer import NestedClientReservationSerializer
from apps.client.api.serializers import PatientSerializer
from apps.client.models import Client
from apps.medcard.models import Action, MedicalCard, Stage
from apps.notifications.models import Notification
from apps.reservation import services
from apps.reservation.models import Reservation
from apps.user.api.nested_serializers import NestedDoctorSerializer
from apps.user.api.serializers import DoctorSerializer, UserSpecializationSerializer
from apps.user.models import User
from apps.work.api.nested_serializers import NestedWorkReservationSerializer
from apps.work.api.serializers import MobileWorkSerializer, WorkDetailSerializer
from apps.work.models import Work


class ReservationSerializer(serializers.ModelSerializer):
    reservation_client = PatientSerializer()
    reservation_doctor = DoctorSerializer()
    reservation_work = WorkDetailSerializer(required=False)
    reservation_date = serializers.DateField(
        format="%d-%m-%Y", input_formats=["%d-%m-%Y"]
    )
    reservation_start_time = serializers.TimeField(
        format="%H:%M", input_formats=["%H:%M"]
    )
    reservation_end_time = serializers.TimeField(
        format="%H:%M", input_formats=["%H:%M"]
    )

    class Meta:
        model = Reservation
        fields = [
            "reservation_id",
            "reservation_client",
            "reservation_doctor",
            "reservation_work",
            "reservation_notes",
            "reservation_date",
            "reservation_start_time",
            "reservation_end_time",
            "is_initial",
            "cancelled",
            "cancelled_by_patient",
            "created_at",
        ]
        extra_kwargs = {
            "cancelled": {"read_only": True},
            "cancelled_by_patient": {"read_only": True},
        }

    def create(self, validated_data):
        request = self.context.get("request")

        current_user = request.user
        if not current_user:
            raise ValidationError("Authentication failed!")

        if not current_user.user_type:
            raise ValidationError(
                _(f"User with id: {current_user.pk} does not have user type")
            )

        reservation_client = validated_data.pop("reservation_client")
        reservation_doctor = validated_data.pop("reservation_doctor")
        reservation_work = validated_data.pop("reservation_work", None)

        client_instance = Client.objects.get(pk=reservation_client.get("client_id"))
        doctor_instance = User.objects.get(pk=reservation_doctor.get("id"))

        if (
            current_user.user_type.type_text == "Доктор"
            and doctor_instance.pk != current_user.pk
        ):
            raise ValidationError(
                "Врач может создать запись только самому себе, обратитесь в регистратуру"
            )

        if not reservation_work:
            work_instance = None
        else:
            work_id = reservation_work.get("work_id", None)
            if work_id:
                work_instance = Work.objects.filter(pk=work_id).first()

                if not work_instance:
                    raise ValidationError(
                        f"Работа с ID: {reservation_work.get('work_id')} не найдена"
                    )

        start_time = validated_data.get("reservation_start_time")
        end_time = validated_data.get("reservation_end_time")
        reservation_date = validated_data.get("reservation_date")

        services.ensure_reservation_available(
            doctor=doctor_instance,
            target_date=reservation_date,
            start_time=start_time,
            end_time=end_time,
        )

        reservation_instance = Reservation(
            reservation_client=client_instance,
            reservation_doctor=doctor_instance,
            reservation_work=work_instance,
            reservation_notes=validated_data.get("reservation_notes"),
            reservation_date=reservation_date,
            reservation_start_time=start_time,
            reservation_end_time=end_time,
            is_initial=validated_data.get("is_initial", False),
        )

        notification_instance = Notification(
            notification_reservation=reservation_instance,
            notification_receiver=doctor_instance,
            notification_message="",
        )

        reservation_instance.save()
        notification_instance.save()

        if reservation_work:
            work_instance = Work.objects.get(pk=reservation_work.get("work_id"))
            medicalcard = MedicalCard.objects.create(
                client=client_instance, card_price=work_instance.work_basic_price
            )
            stage = Stage.objects.create(
                card=medicalcard, stage_created_by=request.user, stage_index=0
            )
            Action.objects.create(
                action_stage=stage,
                action_work=work_instance,
                action_doctor=doctor_instance,
                action_price=work_instance.work_basic_price,
                action_quantity=1,
                action_created_by=request.user,
            )
        return reservation_instance


class ReservationUpdateSerializer(serializers.ModelSerializer):
    reservation_client = PatientSerializer(required=False)
    reservation_doctor = DoctorSerializer(required=False)
    reservation_date = serializers.DateField(
        format="%d-%m-%Y", input_formats=["%d-%m-%Y"], required=False
    )
    reservation_start_time = serializers.TimeField(
        format="%H:%M", input_formats=["%H:%M"], required=False
    )
    reservation_end_time = serializers.TimeField(
        format="%H:%M", input_formats=["%H:%M"], required=False
    )

    class Meta:
        model = Reservation
        fields = [
            "reservation_id",
            "reservation_client",
            "reservation_doctor",
            "reservation_notes",
            "reservation_date",
            "reservation_start_time",
            "reservation_end_time",
            "is_initial",
            "cancelled",
            "cancelled_by_patient",
            "created_at",
        ]
        extra_kwargs = {
            "cancelled": {"read_only": True},
            "cancelled_by_patient": {"read_only": True},
        }

    def update(self, instance, validated_data):
        request = self.context.get("request")

        current_user = request.user
        if not current_user:
            raise ValidationError("Authentication failed!")

        if not current_user.user_type:
            raise ValidationError(
                _(f"User with id: {current_user.pk} does not have user type")
            )

        reservation_client = validated_data.pop("reservation_client", None)
        reservation_doctor = validated_data.pop("reservation_doctor", None)

        client_instance = (
            Client.objects.get(pk=reservation_client.get("client_id"))
            if reservation_client
            else None
        )
        doctor_instance = (
            User.objects.get(pk=reservation_doctor.get("id"))
            if reservation_doctor
            else None
        )
        if doctor_instance:
            if (
                current_user.user_type.type_text == "Доктор"
                and doctor_instance.pk != current_user.pk
            ):
                raise ValidationError(
                    "Врач может создать запись только самому себе, обратитесь в регистратуру"
                )

        start_time = validated_data.get("reservation_start_time", None)
        end_time = validated_data.get("reservation_end_time", None)
        reservation_date = validated_data.get("reservation_date")

        target_doctor = doctor_instance or instance.reservation_doctor
        target_date = reservation_date or instance.reservation_date
        target_start = start_time or instance.reservation_start_time
        target_end = end_time or instance.reservation_end_time

        services.ensure_reservation_available(
            doctor=target_doctor,
            target_date=target_date,
            start_time=target_start,
            end_time=target_end,
            exclude_reservation_id=instance.reservation_id,
        )

        instance.reservation_client = (
            client_instance if client_instance else instance.reservation_client
        )
        instance.reservation_doctor = (
            doctor_instance if doctor_instance else instance.reservation_doctor
        )
        instance.reservation_notes = validated_data.get(
            "reservation_notes", instance.reservation_notes
        )
        instance.reservation_date = validated_data.get(
            "reservation_date", instance.reservation_date
        )
        instance.reservation_start_time = validated_data.get(
            "reservation_start_time", instance.reservation_start_time
        )
        instance.reservation_end_time = validated_data.get(
            "reservation_end_time", instance.reservation_end_time
        )
        instance.is_initial = validated_data.get("is_initial", instance.is_initial)
        instance.save()

        notification_instance = Notification(
            notification_reservation=instance,
            notification_receiver=instance.reservation_doctor,
            notification_message="",
        )
        notification_instance.save()
        return instance


class ReservationForceUpdateSerializer(serializers.ModelSerializer):
    reservation_client = PatientSerializer(required=False)
    reservation_doctor = DoctorSerializer(required=False)
    reservation_date = serializers.DateField(
        format="%d-%m-%Y", input_formats=["%d-%m-%Y"], required=False
    )
    reservation_start_time = serializers.TimeField(
        format="%H:%M", input_formats=["%H:%M"], required=False
    )
    reservation_end_time = serializers.TimeField(
        format="%H:%M", input_formats=["%H:%M"], required=False
    )

    class Meta:
        model = Reservation
        fields = [
            "reservation_id",
            "reservation_client",
            "reservation_doctor",
            "reservation_notes",
            "reservation_date",
            "reservation_start_time",
            "reservation_end_time",
            "is_initial",
            "cancelled",
            "created_at",
        ]

    def update(self, instance, validated_data):
        reservation_client = validated_data.pop("reservation_client", None)
        reservation_doctor = validated_data.pop("reservation_doctor", None)

        client_instance = (
            Client.objects.get(pk=reservation_client.get("client_id"))
            if reservation_client
            else None
        )
        doctor_instance = (
            User.objects.get(pk=reservation_doctor.get("id"))
            if reservation_doctor
            else None
        )

        instance.reservation_client = (
            client_instance if client_instance else instance.reservation_client
        )
        instance.reservation_doctor = (
            doctor_instance if doctor_instance else instance.reservation_doctor
        )
        instance.reservation_notes = validated_data.get(
            "reservation_notes", instance.reservation_notes
        )
        instance.reservation_date = validated_data.get(
            "reservation_date", instance.reservation_date
        )
        instance.reservation_start_time = validated_data.get(
            "reservation_start_time", instance.reservation_start_time
        )
        instance.reservation_end_time = validated_data.get(
            "reservation_end_time", instance.reservation_end_time
        )
        instance.cancelled = validated_data.get("cancelled", instance.cancelled)
        instance.is_initial = validated_data.get("is_initial", instance.is_initial)
        instance.save()

        if not instance.cancelled:
            notification_instance = Notification(
                notification_reservation=instance,
                notification_receiver=instance.reservation_doctor,
                notification_message="",
            )
            notification_instance.save()
        return instance


class ReservationListSerializer(serializers.ModelSerializer):
    reservation_client = NestedClientReservationSerializer(read_only=True)
    reservation_work = NestedWorkReservationSerializer(read_only=True)

    class Meta:
        model = Reservation
        fields = (
            "reservation_id",
            "reservation_doctor",
            "reservation_client",
            "reservation_work",
            "reservation_notes",
            "reservation_date",
            "reservation_start_time",
            "reservation_end_time",
            "is_initial",
            "cancelled",
            "cancelled_by_patient",
            "created_at",
        )


class ReservationDoctorsSerializer(serializers.ModelSerializer):
    user_specialization = UserSpecializationSerializer(many=True, read_only=True)
    status = serializers.SerializerMethodField()
    available_slots_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "user_firstname",
            "user_lastname",
            "user_specialization",
            "user_image",
            "status",
            "available_slots_count",
        )

    def get_status(self, obj):
        request = self.context.get("request")
        if not request:
            return False
        date_str = request.query_params.get("date")
        if not date_str:
            return False
        try:
            target_date = datetime.strptime(date_str, "%d-%m-%Y").date()
        except ValueError:
            return False
        return services.get_working_schedule_for_date(obj, target_date) is not None

    def get_available_slots_count(self, obj):
        request = self.context.get("request")
        if not request:
            return 0
        date_str = request.query_params.get("date")
        if not date_str:
            return 0
        try:
            target_date = datetime.strptime(date_str, "%d-%m-%Y").date()
        except ValueError:
            return 0
        slots = services.build_available_slots(obj, target_date)
        return sum(1 for slot in slots if slot["is_available"])


class ReservationDoctorDetailSerializer(serializers.ModelSerializer):
    user_specialization = UserSpecializationSerializer(many=True, read_only=True)
    available_slots = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "user_firstname",
            "user_lastname",
            "user_specialization",
            "user_image",
            "available_slots",
            "status"
        )

    def get_available_slots(self, obj):
        request = self.context.get('request')
        if not request:
            return []
            
        date_str = request.query_params.get('date')
        if not date_str:
            return []

        try:
            target_date = datetime.strptime(date_str, '%d-%m-%Y').date()
            return services.build_available_slots(obj, target_date)

        except Exception:
            return []

    def get_status(self, obj):
        request = self.context.get("request")
        if not request:
            return False
        date_str = request.query_params.get("date")
        if not date_str:
            return False
        try:
            target_date = datetime.strptime(date_str, "%d-%m-%Y").date()
        except ValueError:
            return False
        return services.get_working_schedule_for_date(obj, target_date) is not None


class MobileReservationDoctorSerializer(ReservationDoctorsSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta(ReservationDoctorsSerializer.Meta):
        fields = ReservationDoctorsSerializer.Meta.fields + ("full_name",)

    def get_full_name(self, obj):
        return obj.full_name()


class MobileReservationDoctorDetailSerializer(ReservationDoctorDetailSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta(ReservationDoctorDetailSerializer.Meta):
        fields = ReservationDoctorDetailSerializer.Meta.fields + ("full_name",)

    def get_full_name(self, obj):
        return obj.full_name()


class MobileReservationDoctorWorkSerializer(MobileWorkSerializer):
    pass


class MobileReservationListSerializer(serializers.ModelSerializer):
    reservation_doctor = NestedDoctorSerializer(read_only=True)
    reservation_work = NestedWorkReservationSerializer(read_only=True)
    request_status = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = [
            "reservation_id",
            "reservation_doctor",
            "reservation_work",
            "reservation_notes",
            "reservation_date",
            "reservation_start_time",
            "reservation_end_time",
            "is_initial",
            "cancelled",
            "cancelled_by_patient",
            "request_status",
            "created_at",
        ]

    def get_request_status(self, obj):
        if hasattr(obj, "reservation_request") and obj.reservation_request:
            return obj.reservation_request.get_status_display()
        return None


class MobileReservationDetailSerializer(MobileReservationListSerializer):
    reservation_client = NestedClientReservationSerializer(read_only=True)

    class Meta(MobileReservationListSerializer.Meta):
        fields = MobileReservationListSerializer.Meta.fields + ["reservation_client"]
