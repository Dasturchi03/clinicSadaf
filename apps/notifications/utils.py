from channels.db import database_sync_to_async
from django.utils import timezone

from .models import Notification, NotificationTypes


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
    NotificationTypes.RESERVATION_CREATED: "Yangi qabul yaratildi",
    NotificationTypes.RESERVATION_APPROVED: "Qabul tasdiqlandi",
    NotificationTypes.RESERVATION_CANCELLED: "Qabul bekor qilindi",
    NotificationTypes.RESERVATION_CANCELLED_BY_PATIENT: "Qabul bemor tomonidan bekor qilindi",
    NotificationTypes.RESERVATION_REQUEST_CREATED: "Qabul so'rovi yuborildi",
    NotificationTypes.RESERVATION_REMINDER: "Qabul eslatmasi",
}


def get_notification_label(notification_type):
    return NOTIFICATION_LABELS.get(notification_type, notification_type)


def build_notification_message(notification_type, reservation=None):
    if notification_type == NotificationTypes.RESERVATION_REQUEST_CREATED:
        return "New reservation request received"
    if notification_type == NotificationTypes.RESERVATION_APPROVED:
        return "Your reservation has been approved"
    if notification_type == NotificationTypes.RESERVATION_CANCELLED:
        return "Your reservation request was cancelled by clinic"
    if notification_type == NotificationTypes.RESERVATION_CANCELLED_BY_PATIENT:
        return "Patient cancelled the reservation"
    if notification_type == NotificationTypes.RESERVATION_REMINDER and reservation:
        return (
            "Reminder: "
            f"{reservation.reservation_date.strftime('%d-%m-%Y')} "
            f"{reservation.reservation_start_time.strftime('%H:%M')}"
        )
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
        message="Reservation approved",
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
    today = timezone.localdate()
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
