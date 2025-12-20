from modeltranslation.translator import register, TranslationOptions
from .models import User_Type


@register(User_Type)
class User_TypeTranslation(TranslationOptions):
    fields = ('type_text',)
