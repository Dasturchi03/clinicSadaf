import django_filters as filters
from django.db import models

from apps.vacancies.models import Vacancy, VacancyApplication


class VacancyFilterSet(filters.FilterSet):
    o = filters.OrderingFilter(
        fields=(
            ("vacancy_id", "vacancy_id"),
            ("sort_order", "sort_order"),
            ("created_at", "created_at"),
        )
    )
    q = filters.CharFilter(method="search", label="Search")
    is_active = filters.BooleanFilter()

    class Meta:
        model = Vacancy
        fields = []

    def search(self, queryset, name, value):
        if value:
            return queryset.filter(title__icontains=value)
        return queryset


class VacancyApplicationFilterSet(filters.FilterSet):
    o = filters.OrderingFilter(
        fields=(
            ("application_id", "application_id"),
            ("created_at", "created_at"),
            ("status", "status"),
        )
    )
    q = filters.CharFilter(method="search", label="Search")
    status = filters.CharFilter()
    vacancy = filters.NumberFilter(field_name="vacancy__vacancy_id")

    class Meta:
        model = VacancyApplication
        fields = []

    def search(self, queryset, name, value):
        if value:
            return queryset.filter(
                models.Q(first_name__icontains=value)
                | models.Q(last_name__icontains=value)
                | models.Q(phone__icontains=value)
                | models.Q(email__icontains=value)
                | models.Q(vacancy__title__icontains=value)
            )
        return queryset
