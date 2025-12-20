import django_filters as filters

from apps.medcard.models import MedicalCard, Xray


class MedicalCardFilter(filters.FilterSet):
    doctor_id = filters.CharFilter(
        method="filter_by_doctor_id", help_text="Provide id of a doctor"
    )
    client = filters.CharFilter(help_text="Provide id of a client")

    class Meta:
        model = MedicalCard
        fields = ["client"]

    def filter_by_doctor_id(self, queryset, value, name):
        if value:
            return queryset.filter(stage__action_stage__action_doctor_id=value)
        return value


class XrayFilter(filters.FilterSet):
    client = filters.NumberFilter(field_name="client", lookup_expr="exact")
    medical_card = filters.NumberFilter(field_name="medical_card", lookup_expr="exact")
    stage = filters.NumberFilter(field_name="stage", lookup_expr="exact")
    tooth = filters.NumberFilter(field_name="tooth", lookup_expr="exact")

    class Meta:
        model = Xray
        fields = []
