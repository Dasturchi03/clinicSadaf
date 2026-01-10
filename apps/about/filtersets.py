from django_filters import rest_framework as filters

from apps.core.choices import ArticleTypes


class ArticleFilterSet(filters.FilterSet):
    article_type = filters.ChoiceFilter(
        field_name='article_type',
        choices=ArticleTypes.choices
    )
