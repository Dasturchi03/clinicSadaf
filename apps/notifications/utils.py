from .models import Notification
from channels.db import database_sync_to_async


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
                "created_at": instance.created_at.strftime("%d-%m-%YT%H:%M"),
            }
            for instance in queryset
        ]
    return list_notifications