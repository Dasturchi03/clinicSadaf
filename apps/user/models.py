import os

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import dateformat, timezone
from django.utils.deconstruct import deconstructible

from apps.core.choices import GenderTypes
from apps.core.countries import COUNTRIES
from apps.specialization.models import Specialization


@deconstructible
class PathAndRename(object):
    # Создание папок с айди модели и переименование загруженной фото по айди и времени

    def __init__(self, sub_path):
        self.path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split(".")[-1]
        if instance.pk:
            formatted_date = dateformat.format(timezone.now(), "d-m-Y_H-i-s")
            filename = "{}__{}.{}".format(instance.pk, formatted_date, ext)
            instance_pk = str(instance.pk)
            if len(instance_pk) != 7:
                n = 7 - len(instance_pk)
                instance_pk = str(0) * n + instance_pk
            else:
                instance_pk = instance_pk

            path_to_users = "{}/users/{}".format(settings.MEDIA_ROOT, instance_pk)
            if os.path.exists(path_to_users):
                path = "users/{}/{}".format(instance_pk, filename)
                return path
            else:
                os.makedirs(path_to_users)
                path = "users/{}/{}".format(instance_pk, filename)
                return path
        else:
            pass


path_and_rename = PathAndRename("users/")


class User_Type(models.Model):
    user_type_id = models.AutoField(primary_key=True)
    type_text = models.CharField(max_length=255)

    deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.type_text

    class Meta:
        verbose_name = "Тип пользователя"
        verbose_name_plural = "Тип пользователей"
        default_permissions = ()
        permissions = [
            ("add_user_type", "Добавить тип пользователя"),
            ("view_user_type", "Просмотреть тип пользователя"),
            ("change_user_type", "Изменить тип пользователя"),
            ("delete_user_type", "Удалить тип пользователя"),
        ]


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, password, **extra_fields):
        """
        Create and save a user with the given username, and password.
        """
        if not username:
            raise ValueError("The given username must be set")
        GlobalUserModel: type[User] = apps.get_model(
            self.model._meta.app_label, self.model._meta.object_name
        )
        username = GlobalUserModel.normalize_username(username)
        user: User = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, password, **extra_fields)

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    user_type = models.ForeignKey(
        User_Type,
        related_name="user_type",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    user_firstname = models.CharField(
        verbose_name="Имя", max_length=50, blank=True, null=True
    )
    user_lastname = models.CharField(
        verbose_name="Фамилия", max_length=50, blank=True, null=True
    )
    user_father_name = models.CharField(
        verbose_name="Отчество", max_length=50, blank=True, null=True
    )
    user_birthdate = models.DateField(
        verbose_name="Дата Рождения", blank=True, null=True
    )
    user_gender = models.CharField(
        verbose_name="Пол",
        max_length=20,
        choices=GenderTypes.choices,
        default=GenderTypes.MALE,
    )
    user_address = models.CharField(
        verbose_name="Адрес", max_length=255, blank=True, null=True
    )
    user_citizenship = models.CharField(
        verbose_name="Гражданство",
        max_length=100,
        choices=COUNTRIES,
        blank=True,
        null=True,
    )
    user_specialization = models.ManyToManyField(
        Specialization,
        verbose_name="Специализация",
        related_name="user_specialization",
        blank=True,
    )
    user_telegram = models.CharField(
        verbose_name="Телеграм", max_length=255, blank=True, null=True
    )
    user_color = models.CharField(
        verbose_name="Цвет", max_length=255, blank=True, null=True
    )
    user_on_place = models.BooleanField(
        verbose_name="На рабочем месте", default=True, blank=True, null=True
    )
    user_is_active = models.BooleanField(verbose_name="Активный", blank=True, null=True)

    user_salary_percent = models.IntegerField(
        verbose_name="Зарплата сотрудника", default=0
    )
    user_salary_child_percent = models.IntegerField(
        verbose_name="Зарплата сотрудника (детский)", default=0
    )

    user_has_car = models.BooleanField(
        verbose_name="Личный Транспорт", default=False, blank=True, null=True
    )
    user_image = models.ImageField(
        verbose_name="Фотография", upload_to=path_and_rename, blank=True, null=True
    )

    user_auth_code = models.CharField(max_length=6, blank=True, null=True)
    user_code_max_try = models.CharField(max_length=1, default=2)
    user_code_period = models.DateTimeField(blank=True, null=True)

    archive = models.BooleanField(default=False, blank=True, null=True)
    deleted = models.BooleanField(default=False, blank=True, null=True)

    updated_at = models.DateTimeField(verbose_name="Обновлён", auto_now=True)
    created_at = models.DateTimeField(verbose_name="Создан", auto_now_add=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.username

    def full_name(self):
        return f"{self.user_firstname} {self.user_lastname}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.username:
            instance_pk = str(self.pk)
            if len(instance_pk) != 7:
                n = 7 - len(instance_pk)
                instance_pk = str(0) * n + instance_pk
            else:
                instance_pk = instance_pk
            self.username = instance_pk
            password = "sadaf" + instance_pk
            self.set_password(password)
            super().save(*args, **kwargs)

    def verify_user(self):
        self.user_is_active = True
        self.user_auth_code = None
        self.user_code_max_try = 2
        self.user_code_period = None
        super().save()

    def reset_password(self, user_password):
        self.user_auth_code = None
        self.set_password(user_password)
        super().save()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        default_permissions = ()
        permissions = [
            ("add_user", "Добавить пользователя"),
            ("view_user", "Просмотреть пользователя"),
            ("change_user", "Изменить пользователя"),
            ("delete_user", "Удалить пользователя"),
            ("view_user_private_info", "Просмотреть приватные данные пользователя"),
            ("change_user_private_info", "Изменить приватные данные пользователя"),
            ("view_user_schedule", "Просмотреть график работы пользователя"),
            ("view_user_permissions", "Просмотреть права доступа пользователя"),
            ("change_user_schedule", "Изменить график работы пользователя"),
            ("change_password", "Изменить пароль пользователя"),
        ]


class User_Public_Phone(models.Model):
    # Модуль публичных контактов админа

    user_phone_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        verbose_name="пользователь",
        on_delete=models.SET_NULL,
        related_name="user_public_phone",
        null=True,
    )
    public_phone = models.CharField(verbose_name="Публичный номер", max_length=255)

    deleted = models.BooleanField(default=False)

    updated_at = models.DateTimeField(verbose_name="Обновлён", auto_now=True)
    created_at = models.DateTimeField(verbose_name="Создан", auto_now_add=True)

    def __str__(self):
        return self.public_phone

    class Meta:
        verbose_name = "Публичный номер пользователя"
        verbose_name_plural = "Публичные номера пользователей"
        default_permissions = ()


class User_Private_Phone(models.Model):
    # Модуль приватных контактов админа

    user_phone_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        verbose_name="пользователь",
        related_name="user_private_phone",
        null=True,
    )
    private_phone = models.CharField(verbose_name="Приватный номер", max_length=255)

    deleted = models.BooleanField(default=False)

    updated_at = models.DateTimeField(verbose_name="Обновлён", auto_now=True)
    created_at = models.DateTimeField(verbose_name="Создан", auto_now_add=True)

    def __str__(self):
        return self.private_phone

    class Meta:
        verbose_name = "Приватный номер пользователя"
        verbose_name_plural = "Приватные номера пользователей"
        default_permissions = ()


class UserSchedule(models.Model):
    schedule_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name="user_schedule", null=True
    )
    day = models.CharField(max_length=100)
    work_start_time = models.TimeField()
    work_end_time = models.TimeField()
    lunch_start_time = models.TimeField(null=True, blank=True)
    lunch_end_time = models.TimeField(null=True, blank=True)
    is_working = models.BooleanField(default=True)
    one_time_update = models.BooleanField(default=False)

    def __str__(self):
        return self.day

    class Meta:
        verbose_name = "График Работы"
        verbose_name_plural = "Графики Работ"
        default_permissions = ()


class UserSalary(models.Model):
    salary_id = models.AutoField(primary_key=True)
    salary_for_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        verbose_name="Пользователь",
        related_name="salary_for_user",
        null=True,
    )
    salary_card = models.ForeignKey(
        "medcard.MedicalCard",
        on_delete=models.SET_NULL,
        verbose_name="Зарплата по медкарте",
        related_name="salary_card",
        blank=True,
        null=True,
    )
    salary_action = models.ForeignKey(
        "medcard.Action",
        on_delete=models.SET_NULL,
        verbose_name="Зарплата за работу медкарты",
        related_name="salary_action",
        blank=True,
        null=True,
    )
    salary_work = models.ForeignKey(
        "work.Work",
        on_delete=models.SET_NULL,
        verbose_name="Зарплата за работу",
        related_name="salary_work",
        blank=True,
        null=True,
    )
    salary_work_type = models.CharField(verbose_name="Тип зарплаты", max_length=100)
    salary_action_price = models.FloatField(
        verbose_name="Цена работы медкарты", blank=True, null=True
    )
    salary_work_price = models.FloatField(
        verbose_name="Цена работы", blank=True, null=True
    )
    salary_amount = models.FloatField(verbose_name="Сумма", blank=True, null=True)
    salary_is_paid = models.BooleanField(default=False)
    updated_at = models.DateTimeField(verbose_name="Обновлён", auto_now=True)
    created_at = models.DateTimeField(verbose_name="Создан", auto_now_add=True)

    def __str__(self):
        try:
            return f"{self.salary_for_user.user_firstname}, {self.salary_for_user.user_lastname}"
        except:
            return ""

    class Meta:
        verbose_name = "Зарплата сотрудников"
        verbose_name_plural = "Зарплаты сотрудников"
        default_permissions = ()
        permissions = [
            ("add_usersalary", "Добавить зарплату сотрудника"),
            ("view_usersalary", "Просмотреть зарплату сотрудника"),
            ("change_usersalary", "Изменить зарплату сотрудника"),
            ("delete_usersalary", "Удалить зарплату сотрудника"),
        ]
