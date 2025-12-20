from django.db import models

from apps.client.models import Client
from apps.user.models import User, UserSalary


class ExpensesType(models.Model):
    expenses_type_id = models.AutoField(primary_key=True)
    type_parent = models.ForeignKey(
        "self",
        verbose_name="Главный тип расхода",
        related_name="type_child",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    expenses_type_title = models.CharField(
        verbose_name="Название под-тип расхода",
        max_length=255,
        blank=True,
        null=True,
        unique=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.expenses_type_title

    class Meta:
        verbose_name = "Тип расхода"
        verbose_name_plural = "Типы расходов"
        default_permissions = ()
        permissions = [
            ("add_expensestype", "Добавить тип расхода"),
            ("view_expensestype", "Просмотреть тип расхода"),
            ("change_expensestype", "Изменить тип расхода"),
            ("delete_expensestype", "Удалить тип расхода"),
        ]


class IncomeType(models.Model):
    parent = models.ForeignKey(
        "self",
        verbose_name="Главный тип дохода",
        related_name="children",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    title = models.CharField(
        verbose_name="Название", max_length=255, blank=True, null=True, unique=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Тип дохода"
        verbose_name_plural = "Типы дохода"
        default_permissions = ()
        permissions = [
            ("add_incometype", "Добавить тип дохода"),
            ("view_incometype", "Просмотреть тип дохода"),
            ("change_incometype", "Изменить тип дохода"),
            ("delete_incometype", "Удалить тип дохода"),
        ]


class FinancialReport(models.Model):
    report_id = models.AutoField(primary_key=True)
    report_expense_type = models.ForeignKey(
        ExpensesType,
        verbose_name="Тип расхода",
        related_name="expense_types",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    report_income_type = models.ForeignKey(
        IncomeType,
        verbose_name="Тип дохода",
        related_name="income_types",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    report_title = models.CharField(
        verbose_name="Название расхода", max_length=255, blank=True, null=True
    )
    report_created_by = models.ForeignKey(
        User,
        verbose_name="Отчет создан пользователем",
        related_name="report_created_by",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    report_for_user = models.ForeignKey(
        User,
        verbose_name="Отчет по пользователю",
        related_name="report_for_user",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    report_for_client = models.ForeignKey(
        Client,
        verbose_name="Отчет по пациенту",
        related_name="report_for_client",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    report_salary = models.ForeignKey(
        UserSalary,
        verbose_name="Отчет по зарплате",
        related_name="report_salary",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    report_card = models.ForeignKey(
        "medcard.MedicalCard",
        on_delete=models.SET_NULL,
        verbose_name="Отчет по медкарте",
        related_name="report_card",
        blank=True,
        null=True,
    )
    report_action = models.ForeignKey(
        "medcard.Action",
        on_delete=models.SET_NULL,
        verbose_name="Отчет за работу медкарты",
        related_name="report_action",
        blank=True,
        null=True,
    )
    report_work = models.ForeignKey(
        "work.Work",
        on_delete=models.SET_NULL,
        verbose_name="Отчет за работу",
        related_name="report_work",
        blank=True,
        null=True,
    )
    report_storage_item = models.ForeignKey(
        "storage.StorageItem",
        on_delete=models.SET_NULL,
        verbose_name="Отчет за склад",
        related_name="storage_items",
        blank=True,
        null=True,
    )
    report_action_price = models.FloatField(
        verbose_name="Цена работы медкарты", blank=True, null=True
    )
    report_work_price = models.FloatField(
        verbose_name="Цена работы", blank=True, null=True
    )
    report_sum = models.FloatField(
        verbose_name="Сумма по которой идет отчет", blank=True, null=True
    )
    report_sum_usd = models.FloatField(
        verbose_name="Сумма по которой идет отчет (USD)", blank=True, null=True
    )
    report_usd_cource = models.FloatField(
        verbose_name="Курс (USD)", blank=True, null=True
    )

    report_note = models.CharField(max_length=512, blank=True, null=True)
    report_salary_work_type = models.CharField(max_length=255, blank=True, null=True)
    report_quantity = models.IntegerField(
        verbose_name="Количество товара", blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Отчет"
        verbose_name_plural = "Отчеты"
        default_permissions = ()
        permissions = [
            ("add_financialreport", "Добавить финансовый отчет"),
            ("view_financialreport", "Просмотреть финансовый отчет"),
            ("change_financialreport", "Изменить финансовый отчет"),
            ("delete_financialreport", "Удалить финансовый отчет"),
        ]
