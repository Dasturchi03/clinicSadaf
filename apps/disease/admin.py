from django.contrib import admin
from .models import Disease
from modeltranslation.admin import TranslationAdmin


class DiseaseAdmin(TranslationAdmin):
    list_display = [
        "disease_id",
        "disease_title",
        "parent",
    ]
    search_fields = ["disease_title"]


admin.site.register(Disease, DiseaseAdmin)
