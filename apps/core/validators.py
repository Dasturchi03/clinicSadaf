import re
from django.core.exceptions import ValidationError


def check_letter(value):
    cyrillic_pattern = r'^[а-яА-Я]+$'
    latin_pattern = r'^[a-zA-Z]+$'

    if not re.match(cyrillic_pattern, value) and not re.match(latin_pattern, value):
        raise ValidationError('Value should contain either Cyrillic or Latin letters')
