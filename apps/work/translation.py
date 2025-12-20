from .models import Work
from modeltranslation.translator import register, TranslationOptions


@register(Work)
class WorkTranslation(TranslationOptions):
    fields = ('work_title',)

