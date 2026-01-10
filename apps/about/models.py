import os

from django.db import models

from apps.core.models import BaseModel
from apps.core.choices import ArticleTypes


class Article(BaseModel):
    # Модуль Статья

    article_id = models.AutoField(primary_key=True)
    article_type = models.CharField(max_length=50, choices=ArticleTypes.choices, verbose_name="Тип статьи")
    article_title = models.CharField(max_length=255, null=True, blank=True, verbose_name="Заголовок статьи")
    article_body = models.TextField(null=True, verbose_name="Текст статьи")


class ArticleImage(BaseModel):
    # Фотографии к статье

    photo_id = models.AutoField(primary_key=True)
    article_image = models.ImageField(upload_to="articles/")
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='images')
