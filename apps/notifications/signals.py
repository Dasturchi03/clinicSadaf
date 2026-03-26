import logging

from .models import Notification
from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.forms.models import model_to_dict

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Notification)
def notification_channels(sender, instance, created, **kwargs):
    if created:
        try:
            channel_layer = get_channel_layer()
            room_group_name = f"notification_{instance.notification_receiver.username}"
            event = {
                "type": "new_notification",
                "room_group_name": room_group_name,
                "notification_message": model_to_dict(instance)
            }
            async_to_sync(channel_layer.group_send)(room_group_name, event)
        except Exception:
            logger.exception(
                "Failed to publish notification event for notification_id=%s",
                instance.notification_id,
            )
