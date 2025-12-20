from django.contrib import admin

from apps.expenses.models import ExpensesType, FinancialReport, IncomeType


class ExpensesTypeAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "type_parent",
        "expenses_type_title",
        "created_at",
    ]


class IncomeTypeAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "parent",
        "title",
        "created_at",
    ]


class FinancialReportAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "report_title",
        "report_expense_type",
        "report_income_type",
        "report_sum",
        "created_at",
    ]
    list_display_links = ["pk", "report_title"]


admin.site.register(ExpensesType, ExpensesTypeAdmin)
admin.site.register(IncomeType, IncomeTypeAdmin)
admin.site.register(FinancialReport, FinancialReportAdmin)
