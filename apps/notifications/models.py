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


class NotificationDevicePlatforms(models.TextChoices):
    ANDROID = "android", "Android"
    IOS = "ios", "iOS"
    WEB = "web", "Web"
    UNKNOWN = "unknown", "Unknown"


class NotificationDevice(models.Model):
    device_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        related_name="notification_devices",
        on_delete=models.CASCADE,
    )
    token = models.CharField(max_length=512, unique=True)
    platform = models.CharField(
        max_length=32,
        choices=NotificationDevicePlatforms.choices,
        default=NotificationDevicePlatforms.UNKNOWN,
    )
    device_uid = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_id}:{self.platform}:{self.device_id}"

    class Meta:
        verbose_name = "Устройство уведомлений"
        verbose_name_plural = "Устройства уведомлений"
        default_permissions = ()
        permissions = [
            ("add_notificationdevice", "Добавить устройство уведомлений"),
            ("view_notificationdevice", "Просмотреть устройство уведомлений"),
            ("change_notificationdevice", "Изменить устройство уведомлений"),
            ("delete_notificationdevice", "Удалить устройство уведомлений"),
        ]
