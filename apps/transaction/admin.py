from django.contrib import admin
from .models import Transaction


class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "transaction_type",
        "transaction_client",
        "transaction_user",
        "transaction_action",
        "transaction_sum",
    ]
    ordering = ['-transaction_created_at']


admin.site.register(Transaction, TransactionAdmin)
