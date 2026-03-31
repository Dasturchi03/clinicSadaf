from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timedelta

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.core.choices import ReservationRequestStatuses
from apps.notifications.utils import (
    create_reservation_approved_notifications,
    create_reservation_cancelled_by_patient_notification,
    create_reservation_cancelled_notification,
)
from apps.user.models import User
from .models import Reservation


DOCTOR_TYPE_NAMES = {"Doctor", "Доктор"}
WEEKDAY_NAMES = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday",
}
ACTIVE_REQUEST_STATUSES = {
    ReservationRequestStatuses.DRAFT,
    ReservationRequestStatuses.APPROVED,
    ReservationRequestStatuses.APPROVED_BY_PATIENT,
}


def _normalize_day(value) -> str:
    return str(value).strip().lower()


def get_weekday_aliases(target_date: date) -> set[str]:
    weekday_index = target_date.weekday()
    weekday_name = WEEKDAY_NAMES[weekday_index]
    return {
        _normalize_day(weekday_index),
        _normalize_day(weekday_name),
        _normalize_day(weekday_name[:3]),
    }


def get_working_schedule_for_date(user: User, target_date: date):
    weekday_aliases = get_weekday_aliases(target_date)
    for schedule in user.user_schedule.all():
        if not schedule.is_working:
            continue
        if _normalize_day(schedule.day) in weekday_aliases:
            return schedule
    return None


def get_doctors_queryset():
    return (
        User.objects.select_related("user_type")
        .prefetch_related("user_specialization", "user_schedule", "reservations")
        .filter(user_type__type_text__in=DOCTOR_TYPE_NAMES)
        .distinct()
    )


def get_doctor_reservations(doctor: User, target_date: date, exclude_reservation_id=None):
    queryset = doctor.reservations.filter(
        reservation_date=target_date,
        cancelled=False,
    ).order_by("reservation_start_time")
    if exclude_reservation_id:
        queryset = queryset.exclude(reservation_id=exclude_reservation_id)
    return queryset


def normalize_slot_minutes(slot_minutes: int | None) -> int:
    if not slot_minutes:
        return 60
    if slot_minutes < 15:
        return 15
    return slot_minutes


def ensure_reservation_available(
    doctor: User,
    target_date: date,
    start_time,
    end_time,
    exclude_reservation_id=None,
):
    if start_time >= end_time:
        raise ValidationError(_("Reservation start time must be less than end time"))

    schedule = get_working_schedule_for_date(doctor, target_date)
    if not schedule:
        raise ValidationError(
            _("Doctor %(doctor)s is not working on %(date)s")
            % {
                "doctor": doctor.full_name(),
                "date": target_date.strftime("%d-%m-%Y"),
            }
        )

    if start_time < schedule.work_start_time or end_time > schedule.work_end_time:
        raise ValidationError(
            _("Selected time is outside doctor's working hours: %(start)s - %(end)s")
            % {
                "start": schedule.work_start_time.strftime("%H:%M"),
                "end": schedule.work_end_time.strftime("%H:%M"),
            }
        )

    if schedule.lunch_start_time and schedule.lunch_end_time:
        overlaps_lunch = not (
            end_time <= schedule.lunch_start_time or start_time >= schedule.lunch_end_time
        )
        if overlaps_lunch:
            raise ValidationError("Selected time intersects with doctor's lunch break")

    reservations = get_doctor_reservations(
        doctor=doctor,
        target_date=target_date,
        exclude_reservation_id=exclude_reservation_id,
    )
    for existing_reservation in reservations:
        existing_start_time = existing_reservation.reservation_start_time
        existing_end_time = existing_reservation.reservation_end_time

        if end_time <= existing_start_time or start_time >= existing_end_time:
            continue

        client_name = (
            f"{existing_reservation.reservation_client.client_firstname} "
            f"{existing_reservation.reservation_client.client_lastname}"
        )
        raise ValidationError(
            _("Selected time is already booked: %(client)s, %(start)s - %(end)s")
            % {
                "client": client_name,
                "start": existing_start_time.strftime("%H:%M"),
                "end": existing_end_time.strftime("%H:%M"),
            }
        )

    return schedule


def build_available_slots(doctor: User, target_date: date, slot_minutes: int = 60):
    schedule = get_working_schedule_for_date(doctor, target_date)
    if not schedule:
        return []

    slot_minutes = normalize_slot_minutes(slot_minutes)
    slot_delta = timedelta(minutes=slot_minutes)
    current_dt = datetime.combine(target_date, schedule.work_start_time)
    end_dt = datetime.combine(target_date, schedule.work_end_time)
    reservations = list(get_doctor_reservations(doctor, target_date))
    slots = []

    while current_dt + slot_delta <= end_dt:
        slot_start_dt = current_dt
        slot_end_dt = current_dt + slot_delta
        slot_start = slot_start_dt.time()
        slot_end = slot_end_dt.time()

        overlaps_lunch = False
        if schedule.lunch_start_time and schedule.lunch_end_time:
            overlaps_lunch = not (
                slot_end <= schedule.lunch_start_time
                or slot_start >= schedule.lunch_end_time
            )

        is_booked = any(
            not (
                slot_end <= reservation.reservation_start_time
                or slot_start >= reservation.reservation_end_time
            )
            for reservation in reservations
        )

        slots.append(
            {
                "start": slot_start.strftime("%H:%M"),
                "end": slot_end.strftime("%H:%M"),
                "is_booked": is_booked,
                "is_available": not overlaps_lunch and not is_booked,
            }
        )
        current_dt = slot_end_dt

    return slots


def build_available_dates_summary(
    doctor: User,
    *,
    year: int,
    month: int,
    slot_minutes: int = 60,
):
    total_days = monthrange(year, month)[1]
    result = []

    for day in range(1, total_days + 1):
        target_date = date(year, month, day)
        schedule = get_working_schedule_for_date(doctor, target_date)
        if not schedule:
            result.append(
                {
                    "date": target_date.strftime("%d-%m-%Y"),
                    "is_working": False,
                    "available_slots_count": 0,
                    "has_available_slots": False,
                }
            )
            continue

        slots = build_available_slots(
            doctor=doctor,
            target_date=target_date,
            slot_minutes=slot_minutes,
        )
        available_slots_count = sum(1 for slot in slots if slot["is_available"])
        result.append(
            {
                "date": target_date.strftime("%d-%m-%Y"),
                "is_working": True,
                "available_slots_count": available_slots_count,
                "has_available_slots": available_slots_count > 0,
            }
        )

    return result


def ensure_request_slot_available(
    client,
    doctor: User,
    target_date: date,
    start_time,
    end_time,
    exclude_request_id=None,
):
    ensure_reservation_available(
        doctor=doctor,
        target_date=target_date,
        start_time=start_time,
        end_time=end_time,
    )

    active_requests = doctor.reservation_requests.filter(
        date=target_date,
        status__in=ACTIVE_REQUEST_STATUSES,
    )
    if exclude_request_id:
        active_requests = active_requests.exclude(pk=exclude_request_id)

    for existing_request in active_requests.select_related("client"):
        if existing_request.time != start_time:
            continue
        if client and existing_request.client_id == client.client_id:
            raise ValidationError("You already have a reservation request for this slot")
        raise ValidationError(_("Selected time already has a pending reservation request"))


def ensure_request_can_be_approved_by_clinic(reservation_request):
    if not reservation_request.doctor:
        raise ValidationError(_("Reservation request does not have a doctor"))
    if reservation_request.status == ReservationRequestStatuses.CANCELLED:
        raise ValidationError(_("Cancelled request cannot be approved"))
    if reservation_request.status == ReservationRequestStatuses.CANCELLED_BY_PATIENT:
        raise ValidationError(_("Patient cancelled this request"))
    if reservation_request.reservation_id:
        raise ValidationError(_("Reservation has already been created for this request"))


@transaction.atomic
def approve_reservation_request_by_clinic(
    reservation_request,
    *,
    end_time,
    is_initial=False,
):
    reservation_request = reservation_request.__class__.objects.select_for_update().select_related(
        "client", "doctor", "reservation_work"
    ).get(pk=reservation_request.pk)

    ensure_request_can_be_approved_by_clinic(reservation_request)
    ensure_reservation_available(
        doctor=reservation_request.doctor,
        target_date=reservation_request.date,
        start_time=reservation_request.time,
        end_time=end_time,
    )

    reservation_instance = Reservation.objects.create(
        reservation_client=reservation_request.client,
        reservation_doctor=reservation_request.doctor,
        reservation_work=reservation_request.reservation_work,
        reservation_notes=reservation_request.note,
        reservation_date=reservation_request.date,
        reservation_start_time=reservation_request.time,
        reservation_end_time=end_time,
        is_initial=is_initial,
    )

    reservation_request.reservation = reservation_instance
    reservation_request.status = ReservationRequestStatuses.APPROVED
    reservation_request.save(update_fields=["reservation", "status", "updated_at"])

    create_reservation_approved_notifications(
        reservation=reservation_instance,
        doctor=reservation_request.doctor,
        client_user=reservation_request.client.client_user
        if reservation_request.client
        else None,
    )
    return reservation_request


@transaction.atomic
def cancel_reservation_request(reservation_request, *, cancelled_by_patient=False):
    reservation_request = reservation_request.__class__.objects.select_for_update().get(
        pk=reservation_request.pk
    )

    if reservation_request.status in {
        ReservationRequestStatuses.CANCELLED,
        ReservationRequestStatuses.CANCELLED_BY_PATIENT,
    }:
        raise ValidationError(_("Reservation request is already cancelled"))

    reservation_request.status = (
        ReservationRequestStatuses.CANCELLED_BY_PATIENT
        if cancelled_by_patient
        else ReservationRequestStatuses.CANCELLED
    )
    reservation_request.save(update_fields=["status", "updated_at"])

    reservation = reservation_request.reservation
    if reservation:
        reservation.cancelled = True
        reservation.cancelled_by_patient = cancelled_by_patient
        reservation.save(update_fields=["cancelled", "cancelled_by_patient"])

    if cancelled_by_patient and reservation_request.doctor:
        create_reservation_cancelled_by_patient_notification(
            reservation=reservation,
            doctor=reservation_request.doctor,
        )
    elif (
        not cancelled_by_patient
        and reservation_request.client
        and reservation_request.client.client_user
    ):
        create_reservation_cancelled_notification(
            reservation=reservation,
            client_user=reservation_request.client.client_user,
        )

    return reservation_request


@transaction.atomic
def approve_reservation_request_by_patient(reservation_request):
    reservation_request = reservation_request.__class__.objects.select_for_update().get(
        pk=reservation_request.pk
    )

    if reservation_request.status != ReservationRequestStatuses.APPROVED:
        raise ValidationError(_("Only approved requests can be confirmed by patient"))
    if not reservation_request.reservation_id:
        raise ValidationError(_("Reservation request has no created reservation"))

    reservation_request.status = ReservationRequestStatuses.APPROVED_BY_PATIENT
    reservation_request.save(update_fields=["status", "updated_at"])
    return reservation_request
