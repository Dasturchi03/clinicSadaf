from django.dispatch import Signal
from .models import WorkHistory
from datetime import datetime, date
from datetime import time


def json_datetime_serializer(obj):
    if isinstance(obj, (datetime, date)):
        serial = obj.isoformat()
        return serial

    if isinstance(obj, time):
        serial = obj.strftime('%H:%M')
        return serial

    raise TypeError("{} is not JSON serializable.".format(obj))


def history_update(sender, instance, created, **kwargs):

    if not created:

        tracked_change = WorkHistory.objects.create(
            user=kwargs.get('user').username if kwargs.get('user') is not None else None,
            changed_pk=instance.pk,
        )

        tracked_change.work_title = instance.work_title
        tracked_change.work_basic_price = instance.work_basic_price
        tracked_change.work_vip_price = instance.work_vip_price
        if instance.work_discount_price is not None:
            tracked_change.work_discount_price = instance.work_discount_price
        else:
            tracked_change.work_discount_price = None

        if instance.work_discount_percent is not None:
            tracked_change.work_discount_percent = instance.work_discount_percent
        else:
            tracked_change.work_discount_percent = None
        tracked_change.save()

    else:
        pass


work_history_signal = Signal()
work_history_signal.connect(receiver=history_update)
