from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

from apps.core.models import BaseModel


class Category(models.Model):
    # Модуль Категории

    category_id = models.AutoField(primary_key=True)
    category_title = models.CharField(verbose_name="Название категории", max_length=150)
    category_icon = models.ImageField(verbose_name="Значок категории", upload_to='categories/')
    updated_at = models.DateTimeField(verbose_name="Обновлён", auto_now=True)
    created_at = models.DateTimeField(verbose_name="Создан", auto_now_add=True)

    def __str__(self):
        return self.category_title

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        default_permissions = ()
        permissions = [
            ("add_category", "Добавить категорию"),
            ("view_category", "Просмотреть категорию"),
            ("change_category", "Изменить категорию"),
            ("delete_category", "Удалить категорию"),
        ]


class PrintOutCategory(BaseModel):
    # Модуль Категории, создан для того чтобы сортировать работы по категориям для распечатки
    name = models.CharField(verbose_name="Название категории", max_length=150)
    order_index = models.IntegerField(
        validators=[MinValueValidator(1)], blank=True, null=True
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория Распечатки"
        verbose_name_plural = "Категории Распечатки"
        constraints = [
            UniqueConstraint(fields=["name"], name="unique_print_out_categories_name")
        ]
        default_permissions = ()
        permissions = [
            ("add_printoutcategory", "Добавить категорию распечатки"),
            ("view_printoutcategory", "Просмотреть категорию распечатки"),
            ("change_printoutcategory", "Изменить категорию распечатки"),
            ("delete_printoutcategory", "Удалить категорию распечатки"),
        ]
