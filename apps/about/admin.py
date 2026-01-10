from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from apps.about.models import Article, ArticleImage


class ArticleImagesInline(admin.StackedInline):
    model = ArticleImage
    fields = ["article_image"]


class ArticleAdmin(TranslationAdmin):
    list_display = ["article_type", "article_title"]

    inlines = [ArticleImagesInline]


admin.site.register(Article, ArticleAdmin)
