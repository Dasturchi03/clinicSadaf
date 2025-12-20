import django_filters as filters
from apps.specialization.models import Specialization


class SpecializationFilterSet(filters.FilterSet):
    o = filters.OrderingFilter(
        fields = (
            ('id', 'Specialization(ID)'),
            ('text', 'SpecializationText'),

        )
    )
    q = filters.CharFilter(
        method='search',
        label='Search',
    )   
    
    class Meta:
        model = Specialization
        fields = []

    def search(self, queryset, name, value):
        
        if value:
            return queryset.filter(specialization_text__icontains=value)
        return queryset


        