from datetime import date, datetime

import django_filters as filters
from django.db.models import Count, Q

from apps.user.models import User, UserSalary


class UserFilterSet(filters.FilterSet):
    q = filters.CharFilter(
        method="search",
        label="Search",
    )
    user_type = filters.CharFilter(
        field_name="user_type__type_text", lookup_expr="icontains"
    )
    reservation = filters.BooleanFilter(
        method="filter_by_reservation",
        help_text="Provide true or 1 argument to order users by reservations",
    )
    reservation_date = filters.DateFilter(
        method="filter_by_date",
        input_formats=["%d-%m-%Y"],
    )

    def search(self, queryset, name, value):
        # search by category title

        if value:
            value_parts = value.strip().split()
            first_name = value_parts[0]
            last_name = value_parts[-1] if len(value_parts) > 1 else ""

            first_name_query = Q(user_firstname__icontains=first_name) | Q(
                user_lastname__icontains=first_name
            )

            if last_name:
                last_name_query = Q(user_firstname__icontains=last_name) | Q(
                    user_lastname__icontains=last_name
                )

                return queryset.filter(first_name_query & last_name_query)
            return queryset.filter(first_name_query)

        return queryset

    class Meta:
        model = User
        fields = ["user_gender"]

    def filter_by_reservation(self, queryset, name, value, **kwargs):
        if value:
            current_date = date.today()
            reservation_date = self.data.get("reservation_date", None)

            if reservation_date:
                current_date = datetime.strptime(reservation_date, "%d-%m-%Y").date()

            queryset = (
                queryset.filter(user_type__type_text="Доктор")
                .annotate(
                    reservations_count=Count(
                        "reservations",
                        filter=Q(reservations__reservation_date=current_date),
                    )
                )
                .order_by("-reservations_count")
            )
        return queryset

    def filter_by_date(self, queryset, name, value, **kwargs):
        return queryset


class UserSalaryFilter(filters.FilterSet):
    q = filters.CharFilter(
        method="search",
        label="Search",
    )
    start_date = filters.DateFilter(
        input_formats=["%d-%m-%Y"], field_name="created_at", lookup_expr="date__gte"
    )
    end_date = filters.DateFilter(
        input_formats=["%d-%m-%Y"], field_name="created_at", lookup_expr="date__lte"
    )
    salary_is_paid = filters.BooleanFilter(
        field_name="salary_is_paid", lookup_expr="exact"
    )

    class Meta:
        model = UserSalary
        fields = []

    def search(self, queryset, name, value):
        if not value:
            return queryset

        value_parts = value.strip().split()
        first_name = value_parts[0]
        last_name = value_parts[-1] if len(value_parts) > 1 else ""

        # Name search
        first_name_query = Q(
            salary_card__client__client_firstname__icontains=first_name
        ) | Q(salary_card__client__client_firstname__icontains=first_name)

        last_name_query = Q()
        if last_name:
            last_name_query = Q(
                salary_card__client__client_firstname__icontains=last_name
            ) | Q(salary_card__client__client_firstname__icontains=last_name)

        name_query = first_name_query & last_name_query

        # Work title search
        work_title_query = Q(salary_work__work_title__icontains=value)

        # Combine both queries with OR condition
        return queryset.filter(name_query | work_title_query)


class DoctorsFilterSet(filters.FilterSet):
    category = filters.CharFilter(
        method="filter_by_category",
        help_text="Категория: ID (например, 3) или название (например, 'Терапевт')"
    )

    def filter_by_category(self, queryset, name, value):
        if not value:
            return queryset

        if str(value).isdigit():
            return queryset.filter(
                user_specialization__work_specialization__category__category_id=int(value)
            ).distinct()

        return queryset.filter(
            user_specialization__work_specialization__category__category_title__iexact=value
        ).distinct()

    class Meta:
        model = User
        fields = ['category']
