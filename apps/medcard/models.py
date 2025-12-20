import os

from django.conf import settings
from django.db import models
from django.utils import dateformat, timezone
from django.utils.deconstruct import deconstructible

from apps.client.models import Client
from apps.core.models import BaseModel
from apps.disease.models import Disease
from apps.medcard.utils import x_ray_uuid_path
from apps.user.models import User
from apps.work.models import Work


@deconstructible
class PathAndRename(object):
    # Создание папок с айди модели и переименование загруженной фото по айди и времени

    def __init__(self, sub_path):
        self.path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split(".")[-1]
        if instance.pk:
            formatted_date = dateformat.format(timezone.now(), "d-m-Y_H-i-s")
            filename = "{}__{}.{}".format(instance.client.pk, formatted_date, ext)
            instance_pk = str(instance.client.pk)
            if len(instance_pk) != 7:
                n = 7 - len(instance_pk)
                instance_pk = str(0) * n + instance_pk
            else:
                instance_pk = instance_pk

            path_to_users = "{}/clients/{}".format(settings.MEDIA_ROOT, instance_pk)
            if os.path.exists(path_to_users):
                path = os.path.join(path_to_users, filename)
                return path
            else:
                os.makedirs(path_to_users)
                path = os.path.join(path_to_users, filename)
                return path
        else:
            pass


path_and_rename = PathAndRename("clients/")


class MedicalCard(models.Model):
    # Модуль мед карты

    card_id = models.AutoField(primary_key=True)
    client = models.ForeignKey(
        "client.Client",
        verbose_name="Карта клиента",
        related_name="medicalcard_client",
        on_delete=models.SET_NULL,
        null=True,
    )
    card_price = models.FloatField(verbose_name="Цена мед-карты", default=0, blank=True)
    card_discount_price = models.FloatField(
        verbose_name="Скидочная цена мед-карты", default=0, blank=True
    )
    card_discount_percent = models.IntegerField(
        verbose_name="Скидочный процент мед-карты", default=0, blank=True
    )
    card_is_done = models.BooleanField(verbose_name="Карта завершена", default=False)
    card_is_paid = models.BooleanField(verbose_name="Карта оплачена", default=False)
    card_is_cancelled = models.BooleanField(default=False)
    card_finished_at = models.DateTimeField(
        verbose_name="Карта завершена (время)", null=True, blank=True
    )

    archive = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    card_updated_at = models.DateTimeField(verbose_name="Обновлён", auto_now=True)
    card_created_at = models.DateTimeField(verbose_name="Создан", auto_now_add=True)

    def __str__(self):
        try:
            return f"{self.client.client_firstname}, {self.client.client_lastname}"
        except AttributeError:
            return ""

    class Meta:
        verbose_name = "Медицинская карта"
        verbose_name_plural = "Медицинские карты"
        default_permissions = ()
        permissions = [
            ("add_medicalcard", "Добавить медицинскую карту"),
            ("view_medicalcard", "Просмотреть медицинскую карту"),
            ("change_medicalcard", "Изменить медицинскую карту"),
            ("delete_medicalcard", "Удалить медицинскую карту"),
            ("change_medicalcard_admin", "Изменить медицинскую карту (админ)"),
            ("change_medicalcard_cashier", "Изменить медицинскую карту (кассир)"),
        ]


class Tooth(models.Model):
    # Модуль Зуба

    TOOTH_TYPE = (
        ("Adult", "Adult"),
        ("Child", "Child"),
    )
    tooth_id = models.AutoField(primary_key=True)
    tooth_type = models.CharField(max_length=50, choices=TOOTH_TYPE)
    tooth_number = models.CharField(max_length=100)
    tooth_image = models.ImageField(upload_to="teeth/")

    archive = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    updated_at = models.DateTimeField(verbose_name="Обновлён", auto_now=True)
    created_at = models.DateTimeField(verbose_name="Создан", auto_now_add=True)

    def __str__(self):
        return self.tooth_number

    class Meta:
        verbose_name = "Зуб"
        verbose_name_plural = "Зубы"
        default_permissions = ()
        permissions = [
            ("add_tooth", "Добавить зуб"),
            ("view_tooth", "Просмотреть зуб"),
            ("change_tooth", "Изменить зуб"),
            ("delete_tooth", "Удалить зуб"),
        ]


class Stage(models.Model):
    # Модуль этапа

    stage_id = models.AutoField(primary_key=True)
    tooth = models.ForeignKey(
        Tooth, related_name="tooth", on_delete=models.SET_NULL, blank=True, null=True
    )
    card = models.ForeignKey(
        MedicalCard, related_name="stage", on_delete=models.CASCADE, null=True
    )
    stage_created_by = models.ForeignKey(
        User,
        related_name="stage_created_by",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    stage_is_done = models.BooleanField(default=False)
    stage_is_paid = models.BooleanField(default=False)
    stage_is_cancelled = models.BooleanField(default=False)
    stage_index = models.PositiveIntegerField()

    archive = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    updated_at = models.DateTimeField(verbose_name="Обновлён", auto_now=True)
    created_at = models.DateTimeField(verbose_name="Создан", auto_now_add=True)

    def __str__(self):
        try:
            return f"{self.stage_id}, {self.card.client.client_firstname}, {self.card.client.client_lastname}"
        except AttributeError:
            return ""

    class Meta:
        verbose_name = "Этап"
        verbose_name_plural = "Этапы"
        default_permissions = ()
        permissions = [
            ("add_stage", "Добавить этап"),
            ("view_stage", "Просмотреть этап"),
            ("change_stage", "Изменить этап"),
            ("delete_stage", "Удалить этап"),
        ]


class Action(models.Model):
    # Модуль работы

    ACTION_PRICE_TYPE = (
        ("Basic", "Basic"),
        ("Vip", "Vip"),
        ("Discount-price", "Discount-price"),
        ("Discount-percent", "Discount-percent"),
        ("Zero", "Zero"),
    )
    action_id = models.AutoField(primary_key=True)
    action_stage = models.ForeignKey(
        Stage, related_name="action_stage", on_delete=models.CASCADE, null=True
    )
    action_work = models.ForeignKey(
        Work,
        related_name="action_work",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    action_doctor = models.ForeignKey(
        User,
        related_name="action_doctor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    action_created_by = models.ForeignKey(
        User,
        related_name="action_created_by",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    action_disease = models.ForeignKey(
        Disease,
        related_name="action_disease",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    action_date = models.ForeignKey(
        "reservation.Reservation",
        related_name="action_date",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    action_note = models.TextField(blank=True)
    action_quantity = models.PositiveIntegerField()
    action_price = models.FloatField(verbose_name="Цена работы", default=0, blank=True)
    action_price_type = models.CharField(
        max_length=50, choices=ACTION_PRICE_TYPE, default="Basic"
    )
    action_is_done = models.BooleanField(default=False)
    action_is_paid = models.BooleanField(default=False)
    action_is_cancelled = models.BooleanField(default=False)
    action_finished_at = models.DateTimeField(
        verbose_name="Завершён", null=True, blank=True
    )

    archive = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    updated_at = models.DateTimeField(verbose_name="Обновлён", auto_now=True)
    created_at = models.DateTimeField(verbose_name="Создан", auto_now_add=True)

    def __str__(self):
        return str(self.action_id)

    class Meta:
        verbose_name = "Работа с карты"
        verbose_name_plural = "Работы с карты"
        default_permissions = ()
        permissions = [
            ("add_action", "Добавить работу с карты"),
            ("view_action", "Просмотреть работу с карты"),
            ("change_action", "Изменить работу с карты"),
            ("delete_action", "Удалить работу с карты"),
        ]


class Xray(BaseModel):
    client = models.ForeignKey(
        to=Client, on_delete=models.CASCADE, related_name="x_rays"
    )
    medical_card = models.ForeignKey(
        to=MedicalCard,
        on_delete=models.CASCADE,
        related_name="x_rays",
        blank=True,
        null=True,
    )
    stage = models.ForeignKey(
        to=Stage, on_delete=models.CASCADE, related_name="x_rays", blank=True, null=True
    )
    tooth = models.ForeignKey(
        to=Tooth, on_delete=models.CASCADE, related_name="x_rays", blank=True, null=True
    )
    image = models.ImageField(upload_to=x_ray_uuid_path)

    class Meta:
        verbose_name = "Рентген"
        verbose_name_plural = "Рентген"
        default_permissions = ()
        permissions = [
            ("add_xray", "Добавить рентген"),
            ("view_xray", "Просмотреть рентген"),
            ("change_xray", "Изменить рентген"),
            ("delete_xray", "Удалить рентген"),
        ]
