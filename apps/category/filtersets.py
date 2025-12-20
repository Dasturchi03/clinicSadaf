import django_filters as filters

from apps.category.models import Category, PrintOutCategory


# Category filter
class CategoryFilterSet(filters.FilterSet):
    o = filters.OrderingFilter(
        fields=(
            ("category_id", "Category(ID)"),
            ("category_title", "CategoryTitle"),
        )
    )
    q = filters.CharFilter(
        method="search",
        label="Search",
    )

    class Meta:
        model = Category
        fields = []

    def search(self, queryset, name, value):
        # search by category title

        if value:
            return queryset.filter(category_title__icontains=value)
        return queryset


class PrintOutCategoryFilterSet(filters.FilterSet):
    o = filters.OrderingFilter(
        fields=(
            ("id", "Category(ID)"),
            ("name", "CategoryTitle"),
        )
    )
    q = filters.CharFilter(
        method="search",
        label="Search",
    )

    class Meta:
        model = PrintOutCategory
        fields = []

    def search(self, queryset, name, value):
        if value:
            return queryset.filter(name__icontains=value)
        return queryset
