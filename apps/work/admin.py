from django.contrib import admin
from .models import Work
from modeltranslation.admin import TranslationAdmin


class WorkAdmin(TranslationAdmin):
    list_display = [
        "work_id",
        "work_title",
        "work_basic_price",
        "work_vip_price"
    ]


admin.site.register(Work, WorkAdmin)
