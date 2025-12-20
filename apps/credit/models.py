from django.db import models
from apps.client.models import Client
from apps.medcard.models import MedicalCard, Action
from apps.user.models import User


CREDIT_TYPE = (
    ("Basic", "Basic"),
    ("Vip", "Vip"),
)


class Credit(models.Model):
    credit_id = models.AutoField(primary_key=True)
    credit_client = models.ForeignKey(Client, verbose_name="Заёмщик", related_name="credit_client", on_delete=models.SET_NULL, null=True, blank=True)
    credit_card = models.ForeignKey(MedicalCard, verbose_name="Медкарта Заёмщика", related_name="credit_card", on_delete=models.SET_NULL, null=True, blank=True)
    credit_action = models.ForeignKey(Action, verbose_name="Кредитованная работа", related_name="credit_action", on_delete=models.SET_NULL, null=True, blank=True)
    credit_user = models.ForeignKey(User, verbose_name="Кем Выдан", related_name="credit_user", on_delete=models.SET_NULL, null=True, blank=True)
    credit_sum = models.FloatField(verbose_name="Остаток к оплате", default=0)
    credit_price = models.FloatField(verbose_name="Сумма к оплате кредита", default=0)
    credit_type = models.CharField(verbose_name="Тип кредита", max_length=100, choices=CREDIT_TYPE, default="Basic")
    credit_note = models.CharField(verbose_name="Примечания", max_length=255, blank=True, null=True)
    credit_is_paid = models.BooleanField(verbose_name="Кредит Погашен", default=False)
    credit_updated_at = models.DateTimeField(verbose_name="Кредит обновлён", auto_now=True)
    credit_created_at = models.DateTimeField(verbose_name="Кредит создан", auto_now_add=True)

    def __str__(self):
        try:
            return f"{self.credit_client.client_firstname}, {self.credit_client.client_lastname}"
        except AttributeError:
            return ""

    class Meta:
        verbose_name = "Кредит"
        verbose_name_plural = "Кредиты"
        default_permissions = ()
        permissions = [
            ("add_credit", "Добавить кредит"),
            ("view_credit", "Просмотреть кредит"),
            ("change_credit", "Изменить кредит"),
            ("delete_credit", "Удалить кредит")
        ]