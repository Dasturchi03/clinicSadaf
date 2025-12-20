import django_filters as filters
from apps.storage.models import Storage, StorageItem, StorageHistory


class StorageItemFilterSet(filters.FilterSet):
    o = filters.OrderingFilter(
        fields = (
            ('item_id', 'Storage(ID)'),
            ('item_name', 'ItemName'),

        )
    )
    q = filters.CharFilter(
        method='search',
        label='Search',
    )   
    
    class Meta:
        model = StorageItem
        fields = []

    def search(self, queryset, name, value):
        
        if value:
            return queryset.filter(item_name__icontains=value)
        return queryset


class StorageFilterSet(filters.FilterSet):
    o = filters.OrderingFilter(
        fields = (
            ('storage_id', 'Storage(ID)'),
        )
    )
    q = filters.CharFilter(
        method='search',
        label='Search',
    )   
    
    class Meta:
        model = Storage
        fields = []

    def search(self, queryset, name, value):
        
        if value:
            return queryset.filter(storage_item__item_name__icontains=value)
        return queryset


class StorageHistoryFilter(filters.FilterSet):
    storage_history_created_for = filters.NumberFilter(
        field_name="storage_history_created_for",
        lookup_expr="exact"
    )
    start_date = filters.DateFilter(
        input_formats=['%d-%m-%Y'], 
        field_name='created_at',
        lookup_expr='date__gte'
    )
    end_date = filters.DateFilter(
        input_formats=['%d-%m-%Y'],
        field_name='created_at',
        lookup_expr='date__lte'
    )
    item_name = filters.CharFilter(
        method="filter_by_item_name",
        help_text="Enter title of storage item, example = 'Бензин' "
    )
    
    class Meta:
        model = StorageHistory
        fields = ["storage_history_created_for"]
    
    def filter_by_item_name(self, queryset, name, value, **kwargs):
        if value:
            return queryset.filter(storage_history_item__storage_item__item_name__icontains=value)
        return queryset