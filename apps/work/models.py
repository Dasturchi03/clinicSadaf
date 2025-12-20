from django.db import models

from apps.category.models import Category, PrintOutCategory
from apps.disease.models import Disease
from apps.specialization.models import Specialization


class Work(models.Model):
    # Модуль работ
    TYPE = (("Common", "Common"), ("Tooth", "Tooth"))
    SALARY_TYPE = (("Fixed", "Fixed"), ("Percent", "Percent"), ("Hybrid", "Hybrid"))
    work_id = models.AutoField(primary_key=True)
    work_type = models.CharField(
        verbose_name="Вид Работы", max_length=100, choices=TYPE
    )
    work_salary_type = models.CharField(
        verbose_name="Вид зарплаты", max_length=100, choices=SALARY_TYPE
    )
    category = models.ManyToManyField(
        Category, verbose_name="Категория", related_name="work_category", blank=True
    )
    print_out_categories = models.ManyToManyField(
        to=PrintOutCategory,
        verbose_name="Категории распечатки",
        related_name="works",
        blank=True,
    )
    disease = models.ManyToManyField(
        Disease, verbose_name="Болезнь", related_name="work_disease", blank=True
    )
    specialization = models.ManyToManyField(
        Specialization,
        verbose_name="Специализация",
        related_name="work_specialization",
        blank=True,
    )
    work_title = models.CharField(verbose_name="Название работы", max_length=200)
    work_basic_price = models.FloatField(
        verbose_name="Базовая цена работы", default=0, blank=True
    )
    work_vip_price = models.FloatField(
        verbose_name="ВИП цена работы", default=0, blank=True
    )
    work_null_price = models.IntegerField(
        verbose_name="Бесплатная цена работы", default=0
    )
    work_discount_percent = models.FloatField(
        verbose_name="Скидочный процент работы", default=0, blank=True
    )
    work_discount_price = models.FloatField(
        verbose_name="Скидочная цена работы", default=0, blank=True
    )

    work_fixed_salary_amount = models.FloatField(
        verbose_name="Сумма фиксированной зарплаты с работы", default=0, blank=True
    )
    work_hybrid_salary_amount = models.FloatField(
        verbose_name="Сумма гибридной зарплаты с работы", default=0, blank=True
    )

    archive = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    updated_at = models.DateTimeField(verbose_name="Обновлён", auto_now=True)
    created_at = models.DateTimeField(verbose_name="Создан", auto_now_add=True)

    def __str__(self):
        return self.work_title

    class Meta:
        verbose_name = "Работа"
        verbose_name_plural = "Работы"
        default_permissions = ()
        permissions = [
            ("add_work", "Добавить работу"),
            ("view_work", "Просмотреть работу"),
            ("change_work", "Изменить работу"),
            ("delete_work", "Удалить работу"),
            ("view_work_private_info", "Просмотреть приватные данные работы"),
            ("change_work_private_info", "Изменить приватные данные работы"),
        ]
