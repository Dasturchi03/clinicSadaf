from modeltranslation.translator import TranslationOptions, register

from apps.category.models import Category, PrintOutCategory


@register(Category)
class CategoryTranslation(TranslationOptions):
    fields = ("category_title",)


@register(PrintOutCategory)
class PrintOutCategoryTranslation(TranslationOptions):
    fields = ("name",)
