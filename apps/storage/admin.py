from django.contrib import admin
from .models import Storage, StorageItem, StorageHistory


class StorageAdmin(admin.ModelAdmin):
    list_display = [
        'pk',
        "storage_item",
        "storage_item_measure",
        "storage_quantity",
        "created_at",
    ]


class StorageItemAdmin(admin.ModelAdmin):
    list_display = [
        'pk',
        "item_name",
        "item_measure",
        "created_at",
    ]


class StorageHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'pk',
        "storage_history_created_for",
        "storage_history_item",
        "storage_history_item_measure",
        "storage_history_item_quantity_before",
        "storage_history_item_quantity",
        "created_at"
    ]


admin.site.register(Storage, StorageAdmin)
admin.site.register(StorageItem, StorageItemAdmin)
admin.site.register(StorageHistory, StorageHistoryAdmin)