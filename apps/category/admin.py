from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from apps.category.models import Category, PrintOutCategory


class CategoryAdmin(TranslationAdmin):
    list_display = ["category_id", "category_title"]


class PrintOutCategoryAdmin(TranslationAdmin):
    list_display = ["pk", "name"]
    list_display_links = ["pk", "name"]


admin.site.register(Category, CategoryAdmin)
admin.site.register(PrintOutCategory, PrintOutCategoryAdmin)
