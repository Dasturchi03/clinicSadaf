import os
from uuid import uuid4

from django.db import models
from django.utils import timezone, dateformat
from django.utils.deconstruct import deconstructible


@deconstructible
class VacancyResumePathAndRename:
    def __init__(self, sub_path):
        self.path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split(".")[-1].lower()
        formatted_date = dateformat.format(timezone.now(), "d-m-Y_H-i-s")
        unique = uuid4().hex[:8]

        vacancy_id = instance.vacancy_id if instance.vacancy_id else "general"
        folder = os.path.join(self.path, f"vacancy_{vacancy_id}")

        filename = f"application__{formatted_date}__{unique}.{ext}"
        return os.path.join(folder, filename)


vacancy_resume_upload_to = VacancyResumePathAndRename("vacancies/resumes")


class VacancyApplicationStatus(models.TextChoices):
    NEW = "new", "Новая"
    IN_REVIEW = "in_review", "На рассмотрении"
    ACCEPTED = "accepted", "Принято"
    REJECTED = "rejected", "Отклонено"


class GenderTypes(models.TextChoices):
    MALE = "male", "Мужской"
    FEMALE = "female", "Женский"


class MaritalStatusTypes(models.TextChoices):
    SINGLE = "single", "Холост / Не замужем"
    MARRIED = "married", "Женат / Замужем"
    DIVORCED = "divorced", "Разведен(а)"
    WIDOWED = "widowed", "Вдовец / Вдова"


class Vacancy(models.Model):
    vacancy_id = models.AutoField(primary_key=True)
    title = models.CharField(verbose_name="Название вакансии", max_length=255)
    description = models.TextField(verbose_name="Описание", blank=True, null=True)
    requirements = models.TextField(verbose_name="Требования", blank=True, null=True)
    responsibilities = models.TextField(verbose_name="Обязанности", blank=True, null=True)
    conditions = models.TextField(verbose_name="Условия", blank=True, null=True)

    salary_from = models.DecimalField(
        verbose_name="Зарплата от", max_digits=12, decimal_places=2, blank=True, null=True
    )
    salary_to = models.DecimalField(
        verbose_name="Зарплата до", max_digits=12, decimal_places=2, blank=True, null=True
    )

    address = models.CharField(verbose_name="Адрес", max_length=255, blank=True, null=True)
    phone = models.CharField(verbose_name="Контактный телефон", max_length=50, blank=True, null=True)
    email = models.EmailField(verbose_name="Контактный email", blank=True, null=True)
    deadline = models.DateField(verbose_name="Срок подачи", blank=True, null=True)

    is_active = models.BooleanField(verbose_name="Активный", default=True)
    sort_order = models.PositiveIntegerField(verbose_name="Порядок сортировки", default=0)

    updated_at = models.DateTimeField(verbose_name="Обновлён", auto_now=True)
    created_at = models.DateTimeField(verbose_name="Создан", auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Вакансия"
        verbose_name_plural = "Вакансии"
        ordering = ["sort_order", "-created_at"]
        default_permissions = ()
        permissions = [
            ("add_vacancy", "Добавить вакансию"),
            ("view_vacancy", "Просмотреть вакансию"),
            ("change_vacancy", "Изменить вакансию"),
            ("delete_vacancy", "Удалить вакансию"),
        ]


class VacancyApplication(models.Model):
    application_id = models.AutoField(primary_key=True)
    vacancy = models.ForeignKey(
        Vacancy,
        related_name="applications",
        on_delete=models.CASCADE,
        verbose_name="Вакансия",
    )

    first_name = models.CharField(verbose_name="Имя", max_length=100)
    last_name = models.CharField(verbose_name="Фамилия", max_length=100)
    middle_name = models.CharField(verbose_name="Отчество", max_length=100, blank=True, null=True)

    phone = models.CharField(verbose_name="Телефон", max_length=50)
    email = models.EmailField(verbose_name="Email", blank=True, null=True)
    address = models.CharField(verbose_name="Адрес", max_length=255, blank=True, null=True)
    birth_date = models.DateField(verbose_name="Дата рождения", blank=True, null=True)

    gender = models.CharField(
        verbose_name="Пол",
        max_length=20,
        choices=GenderTypes.choices,
        blank=True,
        null=True,
    )
    marital_status = models.CharField(
        verbose_name="Семейное положение",
        max_length=20,
        choices=MaritalStatusTypes.choices,
        blank=True,
        null=True,
    )

    message = models.TextField(verbose_name="Сообщение", blank=True, null=True)
    resume_file = models.FileField(
        verbose_name="Резюме",
        upload_to=vacancy_resume_upload_to,
    )

    status = models.CharField(
        verbose_name="Статус",
        max_length=20,
        choices=VacancyApplicationStatus.choices,
        default=VacancyApplicationStatus.NEW,
    )

    updated_at = models.DateTimeField(verbose_name="Обновлён", auto_now=True)
    created_at = models.DateTimeField(verbose_name="Создан", auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} -> {self.vacancy.title}"

    class Meta:
        verbose_name = "Отклик на вакансию"
        verbose_name_plural = "Отклики на вакансии"
        ordering = ["-created_at"]
        default_permissions = ()
        permissions = [
            ("add_vacancyapplication", "Добавить отклик на вакансию"),
            ("view_vacancyapplication", "Просмотреть отклик на вакансию"),
            ("change_vacancyapplication", "Изменить отклик на вакансию"),
            ("delete_vacancyapplication", "Удалить отклик на вакансию"),
        ]
