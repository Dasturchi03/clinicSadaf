import django_filters as filters
from django.db.models import Q

from apps.client.models import Client, ClientAnamnesis
from apps.credit.models import Credit


class ClientFilter(filters.FilterSet):
    q = filters.CharFilter(
        method="search",
        label="Search",
    )
    phone = filters.CharFilter(method="filter_by_phone", label="Phone number")
    client_birthdate = filters.DateFilter(input_formats=["%d-%m-%Y"])
    created_at = filters.DateFilter(
        input_formats=["%d-%m-%Y"],
        method="get_by_created_at",
        help_text="IMPORTANT! To view clients by created at use date format only such as DD-MM-YYYY",
    )
    debt = filters.CharFilter(
        method="get_debt_clients",
        help_text="IMPORTANT! To view clients who have unpaid credits provide the keyword 'debt'",
    )

    class Meta:
        model = Client
        fields = [
            "client_citizenship",
            "client_birthdate",
            "client_gender",
            "client_type",
            "created_at",
        ]

    def search(self, queryset, name, value):
        # search by category title

        if value:
            value_parts = value.strip().split()
            first_name = value_parts[0]
            last_name = value_parts[-1] if len(value_parts) > 1 else ""

            first_name_query = Q(client_firstname__icontains=first_name) | Q(
                client_lastname__icontains=first_name
            )

            if last_name:
                last_name_query = Q(client_firstname__icontains=last_name) | Q(
                    client_lastname__icontains=last_name
                )

                return queryset.filter(first_name_query & last_name_query)
            return queryset.filter(first_name_query)

        return queryset

    def filter_by_phone(self, queryset, name, value):
        # search by category title

        if value:
            return queryset.filter(client_public_phone__public_phone__icontains=value)
        return queryset

    def get_debt_clients(self, queryset, name, value):
        if value == "debt":
            credit_query = Credit.objects.filter(credit_is_paid=False)
            return queryset.filter(credit_client__in=credit_query).distinct()
        return queryset

    def get_by_created_at(self, queryset, name, value):
        return queryset.filter(created_at__date=value)


class ClientAnamnesisFilter(filters.FilterSet):
    client = filters.NumberFilter(field_name="client", lookup_expr="exact")

    class Meta:
        model = ClientAnamnesis
        fields = []
