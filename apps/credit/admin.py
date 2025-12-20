from django.contrib import admin
from .models import Credit


class CreditAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "credit_client",
        "credit_action",
        "credit_sum",
        "credit_price",
        "credit_is_paid"
    ]


admin.site.register(Credit, CreditAdmin)
