import django_filters as filters
from django.db.models import Q

from apps.report.models import MedicalCardReport


class MedicalCardReportFilter(filters.FilterSet):
    search = filters.CharFilter(
        method="search_filter",
        label="Search"
    )
    client = filters.NumberFilter(
        field_name="client",
        lookup_expr="exact"
    )
    doctor = filters.NumberFilter(
        field_name="doctor",
        lookup_expr="exact"
    )
    start_date = filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__gte",
        input_formats=["%d-%m-%Y"]
    )
    end_date = filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__lte",
        input_formats=["%d-%m-%Y"]
    )
    
    class Meta:
        model = MedicalCardReport
        fields = []
    
    def search_filter(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(action__action_work__work_title__icontains=value) |
                Q(client_phone=value) 
            )
        return queryset