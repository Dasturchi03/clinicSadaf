import secrets

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.choices import (
    CashbackEntryTypes,
    ClientTypes,
    GenderTypes,
    HepatitisTypes,
    LoyaltyTiers,
)
from apps.core.countries import COUNTRIES
from apps.core.models import BaseModel
from apps.user.models import User


class Client(models.Model):
    # Модуль клиента
    client_id = models.AutoField(primary_key=True)
    client_user = models.OneToOneField(
        User, related_name="client_user", on_delete=models.SET_NULL, null=True
    )
    client_firstname = models.CharField(verbose_name="Имя", max_length=50)
    client_lastname = models.CharField(verbose_name="Фамилия", max_length=50)
    client_father_name = models.CharField(
        verbose_name="Отчество", max_length=50, blank=True, null=True
    )
    client_birthdate = models.DateField(verbose_name="Дата Рождения")
    client_gender = models.CharField(
        verbose_name="Пол", max_length=10, choices=GenderTypes.choices
    )
    client_address = models.CharField(
        verbose_name="Адрес", max_length=255, blank=True, null=True
    )
    client_citizenship = models.CharField(
        verbose_name="Гражданство", max_length=100, choices=COUNTRIES
    )
    client_telegram = models.CharField(
        verbose_name="Телеграм", max_length=50, blank=True, null=True
    )
    client_type = models.CharField(
        verbose_name="Тип Клиента",
        max_length=15,
        choices=ClientTypes.choices,
        default=ClientTypes.BASIC,
    )
    client_balance = models.FloatField(
        verbose_name="Баланс клиента", default=0, blank=True
    )
    referral_code = models.CharField(max_length=32, unique=True, blank=True, null=True)
    referred_by = models.ForeignKey(
        "self",
        related_name="referred_clients",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    loyalty_tier = models.CharField(
        max_length=20,
        choices=LoyaltyTiers.choices,
        default=LoyaltyTiers.BRONZE,
    )
    cashback_balance = models.FloatField(default=0, blank=True)
    total_spent_amount = models.FloatField(default=0, blank=True)
    client_last_viewed_at = models.DateTimeField(default=timezone.now)
    note = models.CharField(max_length=255, blank=True, null=True)
    archive = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    updated_at = models.DateTimeField(verbose_name="Обновлён", auto_now=True)
    created_at = models.DateTimeField(verbose_name="Создан", auto_now_add=True)

    def __str__(self):
        return f"{self.client_firstname}, {self.client_lastname}"

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self._generate_referral_code()
        return super().save(*args, **kwargs)

    def full_name(self):
        return f"{self.client_firstname} {self.client_lastname}"

    def _generate_referral_code(self):
        while True:
            code = f"SADAF-{secrets.token_hex(4).upper()}"
            if not Client.objects.filter(referral_code=code).exists():
                return code

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"
        default_permissions = ()
        permissions = [
            ("add_client", "Добавить клиента"),
            ("view_client", "Просмотреть клиента"),
            ("change_client", "Изменить клиента"),
            ("delete_client", "Удалить клиента"),
        ]
        # constraints = [
        #     UniqueConstraint(
        #         fields=["client_firstname", "client_lastname", "client_birthdate"],
        #         name="unique_client")
        # ]


class Client_Public_Phone(models.Model):
    # Модуль публичных контактов клиента

    client_phone_id = models.AutoField(primary_key=True)
    client = models.ForeignKey(
        to=Client,
        verbose_name="Клиент",
        on_delete=models.SET_NULL,
        related_name="client_public_phone",
        blank=True,
        null=True,
    )
    public_phone = models.CharField(verbose_name="Публичный номер", max_length=255)

    deleted = models.BooleanField(default=False)

    updated_at = models.DateTimeField(verbose_name="Обновлён", auto_now=True)
    created_at = models.DateTimeField(verbose_name="Создан", auto_now_add=True)

    def __str__(self):
        return self.public_phone

    class Meta:
        verbose_name = "Публичный номер Клиента"
        verbose_name_plural = "Публичные номера Клиентов"
        default_permissions = ()


class ClientAnamnesis(BaseModel):
    client = models.ForeignKey(
        to=Client, on_delete=models.CASCADE, related_name="anamnesis"
    )
    contact_reason = models.CharField(max_length=255, blank=True, null=True)
    treatment_history = models.TextField()
    hiv = models.BooleanField(default=False)
    hepatitis = models.CharField(max_length=50, choices=HepatitisTypes.choices)

    class Meta:
        verbose_name = "Анамнез"
        verbose_name_plural = "Анамнез"
        default_permissions = ()
        permissions = [
            ("add_clientanamnesis", "Добавить анамнез"),
            ("view_clientanamnesis", "Просмотреть анамнез"),
            ("change_clientanamnesis", "Изменить анамнез"),
            ("delete_clientanamnesis", "Удалить анамнез"),
        ]


class CashbackEntry(BaseModel):
    entry_id = models.AutoField(primary_key=True)
    client = models.ForeignKey(
        to=Client,
        related_name="cashback_entries",
        on_delete=models.CASCADE,
    )
    source_transaction = models.OneToOneField(
        "transaction.Transaction",
        related_name="cashback_entry",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    related_client = models.ForeignKey(
        to=Client,
        related_name="related_cashback_entries",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    entry_type = models.CharField(max_length=32, choices=CashbackEntryTypes.choices)
    amount = models.FloatField(default=0)
    balance_after = models.FloatField(default=0)
    note = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Cashback entry"
        verbose_name_plural = "Cashback entries"
        ordering = ["-created_at", "-entry_id"]
