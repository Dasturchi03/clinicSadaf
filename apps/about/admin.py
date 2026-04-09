from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from apps.about.models import Article, ArticleImage, ContractDocument, TermsAndConditions, Contacts


class ArticleImagesInline(admin.StackedInline):
    model = ArticleImage
    fields = ["article_image"]


class ArticleAdmin(TranslationAdmin):
    list_display = ["article_type", "article_title"]

    inlines = [ArticleImagesInline]


admin.site.register(Article, ArticleAdmin)


@admin.register(ContractDocument)
class ContractDocumentAdmin(admin.ModelAdmin):
    list_display = ["contract_id", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["title"]


class TermsConditionsAdmin(TranslationAdmin):
    list_display = ["text_id", "title", "text_type", "text", "is_active", "created_at"]
    list_filter = ["is_active", "text_type"]
    search_fields = ["title"]


admin.site.register(TermsAndConditions, TermsConditionsAdmin)
admin.site.register(Contacts)
