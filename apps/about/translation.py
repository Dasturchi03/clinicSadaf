from modeltranslation.translator import TranslationOptions, register

from apps.about.models import Article, TermsAndConditions


@register(Article)
class ArticleTypeTranslation(TranslationOptions):
    fields = ('article_title', 'article_body')


@register(TermsAndConditions)
class TermsAndConditionsTranslation(TranslationOptions):
    fields = ('text')
