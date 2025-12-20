from modeltranslation.translator import register, TranslationOptions
from .models import Disease


@register(Disease)
class DiseaseTranslation(TranslationOptions):
    fields = ('disease_title',)
