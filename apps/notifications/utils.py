from channels.db import database_sync_to_async
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import Notification, NotificationTypes


def get_current_local_date():
    current_time = timezone.now()
    if timezone.is_aware(current_time):
        return timezone.localtime(current_time).date()
    return current_time.date()


@database_sync_to_async
def filter_notification(user_id):
    queryset = Notification.objects.filter(notification_receiver_id=user_id)
    list_notifications = [
            {
                "notification_id": instance.notification_id,
                "notification_receiver": instance.notification_receiver.id,
                "notification_reservation": (
                    instance.notification_reservation.reservation_id
                    if instance.notification_reservation
                    else None
                ),
                "notification_message": instance.notification_message,
                "notification_type": instance.notification_type,
                "is_read": instance.is_read,
                "status_label": get_notification_label(instance.notification_type),
                "next_action": (
                    "open_reservation"
                    if instance.notification_reservation
                    else "open_notifications"
                ),
                "created_at": instance.created_at.strftime("%d-%m-%YT%H:%M"),
            }
            for instance in queryset
        ]
    return list_notifications


NOTIFICATION_LABELS = {
    NotificationTypes.RESERVATION_CREATED: _("Yangi qabul yaratildi"),
    NotificationTypes.RESERVATION_APPROVED: _("Qabul tasdiqlandi"),
    NotificationTypes.RESERVATION_CANCELLED: _("Qabul bekor qilindi"),
    NotificationTypes.RESERVATION_CANCELLED_BY_PATIENT: _("Qabul bemor tomonidan bekor qilindi"),
    NotificationTypes.RESERVATION_REQUEST_CREATED: _("Qabul so'rovi yuborildi"),
    NotificationTypes.RESERVATION_REMINDER: _("Qabul eslatmasi"),
}


def get_notification_label(notification_type):
    return NOTIFICATION_LABELS.get(notification_type, notification_type)


def build_notification_message(notification_type, reservation=None):
    if notification_type == NotificationTypes.RESERVATION_REQUEST_CREATED:
        return _("New reservation request received")
    if notification_type == NotificationTypes.RESERVATION_APPROVED:
        return _("Your reservation has been approved")
    if notification_type == NotificationTypes.RESERVATION_CANCELLED:
        return _("Your reservation request was cancelled by clinic")
    if notification_type == NotificationTypes.RESERVATION_CANCELLED_BY_PATIENT:
        return _("Patient cancelled the reservation")
    if notification_type == NotificationTypes.RESERVATION_REMINDER and reservation:
        return _("Reminder: %(date)s %(time)s") % {
            "date": reservation.reservation_date.strftime("%d-%m-%Y"),
            "time": reservation.reservation_start_time.strftime("%H:%M"),
        }
    return get_notification_label(notification_type)


def create_notification(
    *,
    receiver,
    notification_type,
    reservation=None,
    message=None,
):
    if not receiver:
        return None
    return Notification.objects.create(
        notification_receiver=receiver,
        notification_reservation=reservation,
        notification_type=notification_type,
        notification_message=message
        or build_notification_message(notification_type, reservation=reservation),
    )


def create_reservation_request_notification(doctor):
    return create_notification(
        receiver=doctor,
        notification_type=NotificationTypes.RESERVATION_REQUEST_CREATED,
    )


def create_reservation_approved_notifications(*, reservation, doctor, client_user):
    create_notification(
        receiver=doctor,
        reservation=reservation,
        notification_type=NotificationTypes.RESERVATION_APPROVED,
        message=_("Reservation approved"),
    )
    create_notification(
        receiver=client_user,
        reservation=reservation,
        notification_type=NotificationTypes.RESERVATION_APPROVED,
    )


def create_reservation_cancelled_notification(*, reservation, client_user):
    return create_notification(
        receiver=client_user,
        reservation=reservation,
        notification_type=NotificationTypes.RESERVATION_CANCELLED,
    )


def create_reservation_cancelled_by_patient_notification(*, reservation, doctor):
    return create_notification(
        receiver=doctor,
        reservation=reservation,
        notification_type=NotificationTypes.RESERVATION_CANCELLED_BY_PATIENT,
    )


def create_reservation_reminder_notification(*, reservation, receiver):
    today = get_current_local_date()
    existing = Notification.objects.filter(
        notification_receiver=receiver,
        notification_reservation=reservation,
        notification_type=NotificationTypes.RESERVATION_REMINDER,
        created_at__date=today,
    ).exists()
    if existing:
        return None
    return create_notification(
        receiver=receiver,
        reservation=reservation,
        notification_type=NotificationTypes.RESERVATION_REMINDER,
    )
