import django_filters as filters

from apps.core.choices import PaymentTypes
from apps.expenses.models import ExpensesType, FinancialReport, IncomeType

choices = (("parent", "parent"), ("child", "child"))


class ExpensesTypeFilter(filters.FilterSet):
    q = filters.CharFilter(
        method="search",
        label="Search",
    )
    type_parent = filters.ChoiceFilter(
        choices=choices,
        method="filter_by_parent_type",
        help_text='IMPORTANT! To get parent expenses items paste "parent" argument, '
        'to get only child expenses items paste "child" argument, '
        "to get ALL items do not provide any arguments",
    )

    class Meta:
        model = ExpensesType
        fields = ["type_parent"]

    def search(self, queryset, name, value):
        # search by category title

        if value:
            return queryset.filter(expenses_type_title__icontains=value)
        return queryset

    def filter_by_parent_type(self, queryset, name, value):
        if value:
            if value == "parent":
                return queryset.filter(type_parent_id=None)
            elif value == "child":
                return queryset.filter(type_parent_id__isnull=False)

        return queryset


class IncomeTypeFilter(filters.FilterSet):
    q = filters.CharFilter(
        method="search",
        label="Search",
    )
    IncomeType = filters.ChoiceFilter(
        choices=choices,
        method="filter_by_parent_type",
        help_text='IMPORTANT! To get parent expenses items paste "parent" argument, '
        'to get only child expenses items paste "child" argument, '
        "to get ALL items do not provide any arguments",
    )

    class Meta:
        model = IncomeType
        fields = []

    def search(self, queryset, name, value):
        # search by category title

        if value:
            return queryset.filter(title__icontains=value)
        return queryset

    def filter_by_parent_type(self, queryset, name, value):
        if value:
            if value == "parent":
                return queryset.filter(parent=None)
            elif value == "child":
                return queryset.filter(parent__isnull=False)

        return queryset


class FinancialReportFilter(filters.FilterSet):
    search = filters.CharFilter(method="search_filter", label="Search")
    payment_type = filters.ChoiceFilter(
        method="filter_by_payment_type", choices=PaymentTypes.choices
    )
    report_expense_type = filters.NumberFilter(
        field_name="report_expense_type", lookup_expr="exact"
    )
    report_income_type = filters.NumberFilter(
        field_name="report_income_type", lookup_expr="exact"
    )
    report_storage_item = filters.NumberFilter(
        field_name="report_storage_item", lookup_expr="exact"
    )
    report_for_user = filters.NumberFilter(
        field_name="report_for_user", lookup_expr="exact"
    )
    report_for_client = filters.NumberFilter(
        field_name="report_for_client", lookup_expr="exact"
    )
    start_date = filters.DateFilter(
        input_formats=["%d-%m-%Y"], field_name="created_at", lookup_expr="date__gte"
    )
    end_date = filters.DateFilter(
        input_formats=["%d-%m-%Y"], field_name="created_at", lookup_expr="date__lte"
    )
    income = filters.BooleanFilter(
        method="filter_by_income",
        help_text="Provide true or 1 argument to retrieve only income financial reports, false or 0 to get expenses reports",
    )

    class Meta:
        model = FinancialReport
        fields = []

    def filter_by_income(self, queryset, name, value):
        if value:
            return queryset.filter(report_expense_type=None)
        if not value:
            return queryset.filter(report_expense_type__isnull=False)
        return queryset

    def search_filter(self, queryset, name, value):
        if value:
            queryset.filter(report_title__icontains=value)
        return queryset

    def filter_by_payment_type(self, queryset, name, value):
        if value:
            queryset.filter(report_title__icontains=value)
        return queryset
