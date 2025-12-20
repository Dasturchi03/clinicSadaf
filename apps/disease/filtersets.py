import django_filters as filters

from apps.disease.models import Disease


choices = (
        ("parent", "parent"),
        ("child", "child")
    )

class DiseaseFilter(filters.FilterSet):
    q = filters.CharFilter(
        method='search',
        label='Search',
    )
    parent = filters.ChoiceFilter(
        choices=choices, 
        method="filter_by_parent",
        help_text="IMPORTANT! To get parent diseases paste 'parent' argument to get only child diseases paste"
        "'child' argument to get ALL diseases do not provide any arguments"
    )
     
    def search(self, queryset, name, value):
        # search by category title
        
        if value:
            return queryset.filter(disease_title__icontains=value)
        return queryset
    
    class Meta:
        model = Disease
        fields = ['parent']
        
    def filter_by_parent(self, queryset, name, value):
        if value:
            if value == "parent":
                return queryset.filter(parent=None)
            elif value == "child":
                return queryset.filter(parent__isnull=False)
        return queryset
