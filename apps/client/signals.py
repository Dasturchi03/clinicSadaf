from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.client.loyalty import reward_cashback_for_transaction
from apps.transaction.models import Transaction


@receiver(post_save, sender=Transaction)
def transaction_cashback_signal(sender, instance, created, **kwargs):
    if not created:
        return
    reward_cashback_for_transaction(instance)
