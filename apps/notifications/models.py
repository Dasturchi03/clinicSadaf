from django.db import models
from apps.user.models import User
from apps.reservation.models import Reservation


class NotificationTypes(models.TextChoices):
    RESERVATION_CREATED = "reservation_created", "Reservation created"
    RESERVATION_APPROVED = "reservation_approved", "Reservation approved"
    RESERVATION_CANCELLED = "reservation_cancelled", "Reservation cancelled"
    RESERVATION_CANCELLED_BY_PATIENT = (
        "reservation_cancelled_by_patient",
        "Reservation cancelled by patient",
    )
    RESERVATION_REQUEST_CREATED = (
        "reservation_request_created",
        "Reservation request created",
    )
    RESERVATION_REMINDER = "reservation_reminder", "Reservation reminder"


class Notification(models.Model):
    notification_id = models.AutoField(primary_key=True)
    notification_receiver = models.ForeignKey(User, verbose_name='Получатель', related_name="notification_receiver", on_delete=models.SET_NULL, null=True)
    notification_reservation = models.ForeignKey(Reservation, verbose_name='Запись', related_name="notification_reservation", on_delete=models.SET_NULL, null=True, blank=True)
    notification_type = models.CharField(
        max_length=64,
        choices=NotificationTypes.choices,
        default=NotificationTypes.RESERVATION_CREATED,
    )
    notification_message = models.CharField(verbose_name="", max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.notification_id)

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        default_permissions = ()
        permissions = [
            ("add_notification", "Добавить уведомление"),
            ("view_notification", "Просмотреть уведомление"),
            ("change_notification", "Изменить уведомление"),
            ("delete_notification", "Удалить уведомление")
        ]
