from modeltranslation.translator import TranslationOptions, register

from apps.about.models import Article


@register(Article)
class ArticleTypeTranslation(TranslationOptions):
    fields = ('article_title', 'article_body')
