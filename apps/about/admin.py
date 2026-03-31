from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from apps.about.models import Article, ArticleImage, ContractDocument


class ArticleImagesInline(admin.StackedInline):
    model = ArticleImage
    fields = ["article_image"]


class ArticleAdmin(TranslationAdmin):
    list_display = ["article_type", "article_title"]

    inlines = [ArticleImagesInline]


admin.site.register(Article, ArticleAdmin)


@admin.register(ContractDocument)
class ContractDocumentAdmin(admin.ModelAdmin):
    list_display = ["contract_id", "title", "doc_type", "is_active", "created_at"]
    list_filter = ["doc_type", "is_active"]
    search_fields = ["title"]
