from django.db import models
from apps.medcard.models import Action
from apps.expenses.models import FinancialReport
from apps.credit.models import Credit
from apps.transaction.models import Transaction
from apps.client.models import Client
from apps.user.models import User, UserSalary


class MedicalCardReport(models.Model):
    client = models.ForeignKey(
        to=Client,
        on_delete=models.SET_NULL,
        related_name="medical_card_reports",
        null=True
    )
    client_name = models.CharField(max_length=255, blank=True, null=True)
    client_phone = models.CharField(max_length=255, blank=True, null=True)
    
    doctor = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        related_name="medical_card_reports",
        null=True
    )
    doctor_name = models.CharField(max_length=255, blank=True, null=True)

    action = models.ForeignKey(
        to=Action,
        on_delete=models.CASCADE,
        related_name="medical_card_reports",
    )
    credits = models.ManyToManyField(
        to=Credit,
        related_name="medical_card_reports"
    )
    financial_reports = models.ManyToManyField(
        to=FinancialReport,
        related_name="medical_card_reports"
    )
    transactions = models.ManyToManyField(
        to=Transaction,
        related_name="medical_card_reports"
    )
    salaries = models.ManyToManyField(
        to=UserSalary,
        related_name="medical_card_reports"
    )
    updated_by = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        related_name="medical_card_reports_updated_by",
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Отчет по медкарте"
        verbose_name_plural = "Отчеты по медкарте"
        default_permissions = ()
        permissions = [
            ("view_medicalcardreport", "Просмотреть финансовый отчет"),
            ("change_medicalcardreport", "Изменить финансовый отчет"),
        ]
