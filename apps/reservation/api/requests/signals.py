from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.core.choices import ReservationRequestStatuses
from apps.reservation.models import ReservationRequest


@receiver(post_save, sender=ReservationRequest)
def invoice_fifo_lifo_trigger(sender, instance, created, **kwargs):
    original_status = getattr(instance, "original_status", None)

    if original_status:
        new_status = instance.status
        handle_status_change(instance, original_status, new_status)


def handle_status_change(instance, original_status, new_status):
    if is_status_change_to_approved(original_status, new_status):
        handle_approved_transition(instance)


def handle_approved_transition(instance):
    pass


def is_status_change_to_approved(original_status, new_status):
    return (
        original_status == ReservationRequestStatuses.DRAFT
        and new_status == ReservationRequestStatuses.APPROVED
    )
