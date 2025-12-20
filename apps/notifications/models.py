from django.db import models
from apps.user.models import User
from apps.reservation.models import Reservation


class Notification(models.Model):
    notification_id = models.AutoField(primary_key=True)
    notification_receiver = models.ForeignKey(User, verbose_name='Получатель', related_name="notification_receiver", on_delete=models.SET_NULL, null=True)
    notification_reservation = models.ForeignKey(Reservation, verbose_name='Запись', related_name="notification_reservation", on_delete=models.SET_NULL, null=True, blank=True)
    notification_message = models.CharField(verbose_name="", max_length=255, blank=True, null=True)
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