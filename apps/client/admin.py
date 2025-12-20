from django.contrib import admin

from .models import Client, Client_Public_Phone


class PublicPhoneAdmin(admin.ModelAdmin):
    # Публичные контакты клиента

    list_display = [
        "pk",
        "client",
        "public_phone",
    ]
    list_display_links = ["pk", "client"]
    search_fields = ["public_phone"]


class ClientAdmin(admin.ModelAdmin):
    # Админка Клиента

    list_display = [
        "pk",
        "client_firstname",
        "client_lastname",
        "client_balance",
        "created_at",
    ]
    list_display_links = ["pk", "client_firstname"]
    search_fields = ["client_firstname", "client_lastname"]


admin.site.register(Client, ClientAdmin)
admin.site.register(Client_Public_Phone, PublicPhoneAdmin)
