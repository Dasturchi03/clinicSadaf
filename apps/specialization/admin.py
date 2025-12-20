from django.contrib import admin
from .models import Specialization
from modeltranslation.admin import TranslationAdmin


class SpecializationAdmin(TranslationAdmin):
    list_display = [
        "pk",
        "specialization_text",
        "created_at"
    ]


admin.site.register(Specialization, SpecializationAdmin)

