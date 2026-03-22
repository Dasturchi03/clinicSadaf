from __future__ import annotations

from datetime import date, datetime, timedelta

from rest_framework.exceptions import ValidationError

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
        raise ValidationError("Reservation start time must be less than end time")

    schedule = get_working_schedule_for_date(doctor, target_date)
    if not schedule:
        raise ValidationError(
            f"Doctor {doctor.full_name()} is not working on {target_date.strftime('%d-%m-%Y')}"
        )

    if start_time < schedule.work_start_time or end_time > schedule.work_end_time:
        raise ValidationError(
            f"Selected time is outside doctor's working hours: "
            f"{schedule.work_start_time.strftime('%H:%M')} - {schedule.work_end_time.strftime('%H:%M')}"
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
            f"Selected time is already booked: {client_name}, "
            f"{existing_start_time.strftime('%H:%M')} - {existing_end_time.strftime('%H:%M')}"
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
