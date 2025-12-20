from django.db import models

from apps.client.models import Client
from apps.core.choices import ReservationRequestStatuses
from apps.core.models import BaseModel
from apps.user.models import User
from apps.work.models import Work


class Reservation(models.Model):
    reservation_id = models.AutoField(primary_key=True)
    reservation_client = models.ForeignKey(
        Client,
        verbose_name="Пациент",
        related_name="reservation_client",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    reservation_doctor = models.ForeignKey(
        User,
        verbose_name="Доктор",
        related_name="reservations",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    reservation_work = models.ForeignKey(
        Work,
        verbose_name="Работа",
        related_name="reservation_work",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    reservation_notes = models.CharField(
        verbose_name="Примечания", max_length=255, blank=True, null=True
    )
    reservation_date = models.DateField(verbose_name="Дата резерва")
    reservation_start_time = models.TimeField(verbose_name="Время резерва")
    reservation_end_time = models.TimeField(verbose_name="Время резерва конец")
    # this field determines either patient is new commer or not
    is_initial = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)
    cancelled_by_patient = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.reservation_client.client_firstname

    class Meta:
        verbose_name = "Запись"
        verbose_name_plural = "Записи"
        default_permissions = ()
        permissions = [
            ("add_reservation", "Добавить запись"),
            ("view_reservation", "Просмотреть запись"),
            ("change_reservation", "Изменить запись"),
            ("delete_reservation", "Удалить запись"),
        ]


class ReservationRequest(BaseModel):
    flutter_reservation_id = models.CharField(
        unique=True, max_length=255, blank=True, null=True
    )
    reservation = models.OneToOneField(
        to=Reservation,
        verbose_name="Запись",
        related_name="reservation_request",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    client = models.ForeignKey(
        to=Client,
        verbose_name="Пациент",
        related_name="reservation_requests",
        on_delete=models.CASCADE,
    )
    doctor = models.ForeignKey(
        to=User,
        verbose_name="Доктор",
        related_name="reservation_requests",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=255,
        choices=ReservationRequestStatuses.choices,
        default=ReservationRequestStatuses.DRAFT,
    )
    doctor_name = models.CharField(max_length=255, blank=True, null=True)
    note = models.CharField(
        verbose_name="Примечания", max_length=255, blank=True, null=True
    )
    date = models.DateField(verbose_name="Дата резерва")
    time = models.TimeField(verbose_name="Время резерва")

    class Meta:
        verbose_name = "Запрос на запись"
        verbose_name_plural = "Запросы на запись"
        default_permissions = ()
        permissions = [
            ("add_reservation", "Добавить запись"),
            ("view_reservation", "Просмотреть запись"),
            ("change_reservation", "Изменить запись"),
            ("delete_reservation", "Удалить запись"),
        ]
