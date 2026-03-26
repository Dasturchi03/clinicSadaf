import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.reservation.models import ReservationRequest

from .models import Reservation

logger = logging.getLogger(__name__)

# @receiver(pre_save, sender=ReservationRequest)
# def capture_original_status(sender, instance, **kwargs):
#     try:
#         original_instance = sender.objects.filter(pk=instance.pk).first()

#         if instance.status != original_instance.status:
#             setattr(instance, "original_status", original_instance.status)
#     except sender.DoesNotExist:
#         pass


@receiver(post_save, sender=Reservation)
def reservation_channels(sender, instance, created, **kwargs):
    try:
        channel_layer = get_channel_layer()
        room_group_name = f"reservation_{instance.reservation_doctor.username}"
        event = {
            "type": "new_reservation" if created else "edit_reservation",
            "room_group_name": room_group_name,
            "reservation_instance": {
                "reservation_id": instance.reservation_id,
                "reservation_client": instance.reservation_client.client_id,
                "reservation_doctor": instance.reservation_doctor.id,
                "reservation_notes": instance.reservation_notes,
                "reservation_date": instance.reservation_date.strftime("%d-%m-%Y"),
                "reservation_start_time": instance.reservation_start_time.strftime(
                    "%H:%M"
                ),
                "reservation_end_time": instance.reservation_end_time.strftime("%H:%M"),
                "cancelled": instance.cancelled,
                "created_at": instance.created_at.strftime("%d-%m-%YT%H:%M"),
            },
        }
        async_to_sync(channel_layer.group_send)(room_group_name, event)
    except Exception:
        logger.exception(
            "Failed to publish reservation event for reservation_id=%s",
            instance.reservation_id,
        )
