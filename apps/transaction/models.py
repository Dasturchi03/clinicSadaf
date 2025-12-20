import uuid

from django.db import models

from apps.client.models import Client
from apps.core.choices import PaymentTypes, TransactionTypes
from apps.credit.models import Credit
from apps.expenses.models import FinancialReport
from apps.medcard.models import Action, MedicalCard
from apps.user.models import User


class Transaction(models.Model):
    transaction_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, unique=True
    )
    transaction_type = models.CharField(
        verbose_name="Тип Транзакции", max_length=100, choices=TransactionTypes.choices
    )
    transaction_payment_type = models.CharField(
        verbose_name="Тип Оплаты",
        max_length=50,
        choices=PaymentTypes.choices,
        default=PaymentTypes.CASH,
    )
    transaction_client = models.ForeignKey(
        to=Client,
        verbose_name="Клиент",
        related_name="transaction_client",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    transaction_receiver = models.ForeignKey(
        to=Client,
        verbose_name="Получатель",
        related_name="transaction_receiver",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    transaction_user = models.ForeignKey(
        to=User,
        verbose_name="Пользователь",
        related_name="transaction_user",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        to=User,
        verbose_name="Обновлен пользователем",
        related_name="transactions_updated_by",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    transaction_card = models.ForeignKey(
        to=MedicalCard,
        verbose_name="Медкарта клиента",
        related_name="transaction_card",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    transaction_action = models.ForeignKey(
        to=Action,
        verbose_name="Работа клиента",
        related_name="transaction_action",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    transaction_credit = models.ForeignKey(
        to=Credit,
        verbose_name="Транзакция за кредит",
        related_name="transaction_credit",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    financial_report = models.ForeignKey(
        to=FinancialReport,
        verbose_name="Финансовый отчет",
        related_name="transactions",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    transaction_sum = models.FloatField(
        verbose_name="Сумма полученных денег", default=0, blank=True
    )
    transaction_action_price = models.FloatField(
        verbose_name="Сумма к оплате", default=0, blank=True
    )
    transaction_discount_price = models.FloatField(
        verbose_name="Сумма скидки", default=0, blank=True
    )
    transaction_discount_percent = models.IntegerField(
        verbose_name="Процент скидки", default=0, blank=True
    )
    transaction_work_basic_price = models.FloatField(
        verbose_name="Цена работы", default=0, blank=True
    )
    transaction_work_vip_price = models.FloatField(
        verbose_name="Цена работы (vip)", default=0, blank=True
    )
    transaction_work_discount_price = models.FloatField(
        verbose_name="Сумма скидки работы", default=0, blank=True
    )
    transaction_work_discount_percent = models.IntegerField(
        verbose_name="Процент скидки работы", default=0, blank=True
    )
    transaction_card_discount_price = models.FloatField(
        verbose_name="Сумма скидки с мед-карты", default=0, blank=True
    )
    transaction_card_discount_percent = models.IntegerField(
        verbose_name="Процент скидки с мед-карты", default=0, blank=True
    )
    transaction_benefit = models.FloatField(
        verbose_name="Прибыль с работы", default=0, blank=True
    )
    transaction_loss = models.FloatField(
        verbose_name="Утеря денег с работы", default=0, blank=True
    )
    comment = models.CharField(max_length=255, blank=True, null=True)
    transaction_created_at = models.DateTimeField(
        verbose_name="Транзакция создана", auto_now_add=True
    )
    transaction_updated_at = models.DateTimeField(
        verbose_name="Транзакция обновлена", auto_now=True
    )

    def __str__(self):
        try:
            return f"{self.transaction_client.client_firstname}, {self.transaction_client.client_lastname}"
        except AttributeError:
            return ""

    class Meta:
        verbose_name = "Транзакция"
        verbose_name_plural = "Транзакции"
        default_permissions = ()
        permissions = [
            ("add_transaction", "Добавить транзакцию"),
            ("view_transaction", "Просмотреть транзакцию"),
            ("change_transaction", "Изменить транзакцию"),
            ("delete_transaction", "Удалить транзакцию"),
        ]
