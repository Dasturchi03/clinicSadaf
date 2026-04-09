from django.db import models

from apps.core.models import BaseModel
from apps.core.choices import ArticleTypes, TermsAndConditionsChoices


class Article(BaseModel):
    # Модуль Статья

    article_id = models.AutoField(primary_key=True)
    article_type = models.CharField(max_length=50, choices=ArticleTypes.choices, verbose_name="Тип статьи")
    article_title = models.CharField(max_length=255, null=True, blank=True, verbose_name="Заголовок статьи")
    article_body = models.TextField(null=True, blank=True, verbose_name="Текст статьи")


class ArticleImage(BaseModel):
    # Фотографии к статье

    photo_id = models.AutoField(primary_key=True)
    article_image = models.ImageField(upload_to="articles/")
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='images')


class ContractDocument(BaseModel):
    contract_id = models.AutoField(primary_key=True)
    file = models.FileField(upload_to="contracts/")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"File: {self.contract_id}"


class TermsAndConditions(BaseModel):
    text_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    text_type = models.CharField(
        max_length=50,
        choices=TermsAndConditionsChoices.choices,
        default=TermsAndConditionsChoices.PRIVACY_POLICY,
    )
    text = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_text_type_display()}: {self.title}"


class Contacts(BaseModel):
    data_id = models.AutoField(primary_key=True)
    address = models.TextField()
    location_latt = models.CharField(max_length=20)
    location_long = models.CharField(max_length=20)
    phone = models.CharField(max_length=15)
    telegram = models.CharField(max_length=15, null=True, blank=True)
    facebook = models.CharField(max_length=15, null=True, blank=True)
    instagram = models.CharField(max_length=15, null=True, blank=True)
    youtube = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return f"{self.address}"
