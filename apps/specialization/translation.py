from .models import Specialization
from modeltranslation.translator import register, TranslationOptions


@register(Specialization)
class ToothTranslation(TranslationOptions):
    fields = ('specialization_text',)
