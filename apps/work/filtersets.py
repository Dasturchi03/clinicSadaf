import django_filters as filters
from apps.work.models import Work


class WorkFilterSet(filters.FilterSet):
    q = filters.CharFilter(
        method='search',
        label='Search',
    )
    
    class Meta:
        model = Work
        fields = ["work_type"]
        

    def search(self, queryset, name, value):
        # search by category title
        
        if value:
            return queryset.filter(work_title__icontains=value)
        return queryset