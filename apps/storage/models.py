from django.db import models
from apps.user.models import User


class StorageItem(models.Model):
    item_id = models.AutoField(primary_key=True)
    item_created_by = models.ForeignKey(User, related_name="item_created_by", on_delete=models.SET_NULL, null=True, blank=True)
    item_name = models.CharField(max_length=255, verbose_name="Название мед. материала", blank=True, null=True)
    item_measure = models.CharField(max_length=255, verbose_name="Единица измерения", blank=True, null=True)
    deleted = models.BooleanField(default=False)
    updated_at = models.DateTimeField(verbose_name='Обновлён', auto_now=True)
    created_at = models.DateTimeField(verbose_name='Создан', auto_now_add=True)

    def __str__(self):
        return self.item_name

    class Meta:
        verbose_name = "Мед. материал"
        verbose_name_plural = "Мед. материалы"
        default_permissions = ()
        permissions = [
            ("add_storageitem", "Добавить мед.материал"),
            ("view_storageitem", "Просмотреть мед.материал"),
            ("change_storageitem", "Изменить мед.материал"),
            ("delete_storageitem", "Удалить мед.материал")
        ]


class Storage(models.Model):
    storage_id = models.AutoField(primary_key=True)
    storage_created_by = models.ForeignKey(User, related_name="storage_created_by", on_delete=models.SET_NULL, null=True, blank=True)
    storage_item = models.ForeignKey(StorageItem, verbose_name="Мед. материал", related_name="storage_item", on_delete=models.SET_NULL, blank=True, null=True)
    storage_item_measure = models.CharField(max_length=255, verbose_name="Единица измерения", blank=True, null=True)
    storage_quantity = models.FloatField(verbose_name="Количество", blank=True, null=True)
    deleted = models.BooleanField(default=False)
    updated_at = models.DateTimeField(verbose_name='Обновлён', auto_now=True)
    created_at = models.DateTimeField(verbose_name='Создан', auto_now_add=True)

    def __str__(self):
        try:
            return self.storage_item.item_name
        except AttributeError:
            return ""

    class Meta:
        verbose_name = "Склад"
        verbose_name_plural = "Склад"
        default_permissions = ()
        permissions = [
            ("add_storage", "Добавить в склад"),
            ("view_storage", "Просмотреть склад"),
            ("change_storage", "Изменить склад"),
            ("delete_storage", "Удалить склад")
        ]


class StorageHistory(models.Model):
    HISTORY_TYPE = (
        ("add_quantity", "add_quantity"),
        ("minus_quantity", "minus_quantity"),
        ("give_item", "give_item"),
        ("delete", "delete"),
    )
    storage_history_id = models.AutoField(primary_key=True)
    storage_history_type = models.CharField(max_length=100, choices=HISTORY_TYPE, blank=True, default="")
    storage_history_created_by = models.ForeignKey(User, related_name="storage_history_created_by", on_delete=models.SET_NULL, null=True, blank=True)
    storage_history_created_for = models.ForeignKey(User, related_name="storage_history_created_for", on_delete=models.SET_NULL, null=True, blank=True)
    storage_history_item = models.ForeignKey(Storage, verbose_name="Мед. материал", related_name="storage_history_item", on_delete=models.SET_NULL, null=True, blank=True)
    storage_history_item_measure = models.CharField(max_length=255, verbose_name="Единица измерения", blank=True, null=True)
    storage_history_item_quantity = models.FloatField(verbose_name="Количество", blank=True, null=True)
    storage_history_item_quantity_before = models.FloatField(verbose_name="Количество до", blank=True, null=True)
    updated_at = models.DateTimeField(verbose_name='Обновлён', auto_now=True)
    created_at = models.DateTimeField(verbose_name='Создан', auto_now_add=True)

    def __str__(self):
        try:
            return self.storage_history_item.storage_item.item_name
        except AttributeError:
            return ""

    class Meta:
        verbose_name = "Отчет склада"
        verbose_name_plural = "Отчет склад"
        default_permissions = ()
        permissions = [
            ("add_storagehistory", "Добавить отчет склада"),
            ("view_storagehistory", "Просмотреть отчет склада"),
            ("change_storagehistory", "Изменить отчет склада"),
            ("delete_storagehistory", "Удалить отчет склада")
        ]
