from datetime import datetime, timedelta

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.client.api.nested_serializer import NestedClientReservationSerializer
from apps.client.api.serializers import PatientSerializer
from apps.client.models import Client
from apps.medcard.models import Action, MedicalCard, Stage
from apps.notifications.models import Notification
from apps.reservation.models import Reservation
from apps.user.api.serializers import DoctorSerializer, UserSpecializationSerializer
from apps.user.models import User
from apps.work.api.nested_serializers import NestedWorkReservationSerializer
from apps.work.api.serializers import WorkDetailSerializer
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

        doctor_schedule = doctor_instance.user_schedule.filter(
            day=reservation_date.weekday()
        ).first()

        if doctor_schedule and not doctor_schedule.is_working:
            raise ValidationError(
                f"Запись не создана. У доктора: {doctor_instance.user_firstname}, {doctor_instance.user_lastname} выходной день: {reservation_date}"
            )

        if start_time >= end_time:
            msg = "Reservation start time must be less then end time"
            raise ValidationError(msg)

        reservations = Reservation.objects.filter(
            reservation_doctor=doctor_instance,
            reservation_date=reservation_date,
            cancelled=False,
        )

        if reservations.exists():
            for existing_reservation in reservations:
                existing_start_time = existing_reservation.reservation_start_time
                existing_end_time = existing_reservation.reservation_end_time

                if end_time <= existing_start_time or start_time >= existing_end_time:
                    continue

                client_name = (
                    existing_reservation.reservation_client.client_firstname
                    + " "
                    + existing_reservation.reservation_client.client_lastname
                )
                msg = f"Запись на это время уже назначена: {client_name}, начало: {existing_start_time}, конец: {existing_end_time}"
                raise ValidationError(msg)

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

        doctor_schedule = doctor_instance.user_schedule.filter(
            day=reservation_date.weekday()
        ).first()

        if doctor_schedule and not doctor_schedule.is_working:
            raise ValidationError(
                f"Запись не создана. У доктора: {doctor_instance.user_firstname}, {doctor_instance.user_lastname} выходной день: {reservation_date}"
            )

        if start_time and end_time and start_time >= end_time:
            raise ValidationError("Reservation start time must be less than end time")

        reservations = Reservation.objects.filter(
            reservation_doctor=doctor_instance,
            reservation_date=reservation_date,
            cancelled=False,
        )

        if reservations.exists():

            for existing_reservation in reservations:

                existing_start_time = existing_reservation.reservation_start_time
                existing_end_time = existing_reservation.reservation_end_time

                client_name = (
                    existing_reservation.reservation_client.client_firstname
                    + " "
                    + existing_reservation.reservation_client.client_lastname
                )
                msg = f"Запись на это время уже назначена: {client_name}, начало: {existing_start_time}, конец: {existing_end_time}"

                if (
                    end_time <= existing_start_time
                    or start_time >= existing_end_time
                    or instance.pk == existing_reservation.pk
                ):
                    continue

                client_name = (
                    existing_reservation.reservation_client.client_firstname
                    + " "
                    + existing_reservation.reservation_client.client_lastname
                )
                raise ValidationError(msg)

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
    status = serializers.BooleanField()

    class Meta:
        model = User
        fields = (
            "id",
            "user_firstname",
            "user_lastname",
            "user_specialization",
            "user_image",
            "status"
        )

    def get_status(self, obj):
        request = self.context.get('request')
        date_str = request.query_params.get('date') if request else None

        if not date_str:
            raise ValidationError("Дата не выбран")

        try:
            target_date = datetime.strptime(date_str, '%d-%m-%Y')

            schedule = obj.user_schedule.filter(day__iexact=str(target_date.weekday())).first()

            if schedule and schedule.is_working:
                return True
            return False

        except ValueError:
            return "Ошибка формата даты"


class ReservationDoctorDetailSerializer(serializers.ModelSerializer):
    user_specialization = UserSpecializationSerializer(many=True, read_only=True)
    available_slots = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "user_firstname",
            "user_lastname",
            "user_specialization",
            "user_image",
            "available_slots"
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
            weekday_num = str(target_date.weekday())

            schedule = obj.user_schedule.filter(day__iexact=weekday_num, is_working=True).first()
            if not schedule:
                return []

            booked_reservations = obj.reservations.filter(
                reservation_date=target_date,
                cancelled=False
            ).values('reservation_start_time', 'reservation_end_time')

            slots = []
            current_dt = datetime.combine(target_date, schedule.work_start_time)
            end_dt = datetime.combine(target_date, schedule.work_end_time)

            while current_dt < end_dt:
                slot_start = current_dt.time()
                next_dt = current_dt + timedelta(hours=1)
                
                if next_dt > end_dt:
                    break
                    
                slot_end = next_dt.time()

                is_lunch = False
                if schedule.lunch_start_time and schedule.lunch_end_time:
                    if not (slot_start >= schedule.lunch_end_time or slot_end <= schedule.lunch_start_time):
                        is_lunch = True

                is_booked = any(
                    res['reservation_start_time'] < slot_end and 
                    res['reservation_end_time'] > slot_start 
                    for res in booked_reservations
                )

                if not is_lunch:
                    slots.append({
                        "start": slot_start.strftime("%H:%M"),
                        "end": slot_end.strftime("%H:%M"),
                        "is_booked": is_booked
                    })
                
                current_dt = next_dt

            return slots

        except Exception:
            return []
