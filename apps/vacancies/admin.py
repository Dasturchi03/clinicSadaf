from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from .models import Vacancy, VacancyApplication


@admin.register(Vacancy)
class VacancyAdmin(TranslationAdmin):
    list_display = [
        "vacancy_id",
        "title",
        "is_active",
        "sort_order",
        "created_at",
    ]
    list_filter = ["is_active", "created_at"]
    search_fields = ["title", "title_ru", "title_en", "title_uz"]


@admin.register(VacancyApplication)
class VacancyApplicationAdmin(admin.ModelAdmin):
    list_display = [
        "application_id",
        "vacancy",
        "first_name",
        "last_name",
        "phone",
        "status",
        "created_at",
    ]
    list_filter = ["status", "gender", "marital_status", "created_at"]
    search_fields = ["first_name", "last_name", "phone", "email"]
    autocomplete_fields = ["vacancy"]
