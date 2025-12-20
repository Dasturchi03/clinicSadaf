from django.urls import path

from apps.core.api.router import BaseRouter
from apps.expenses.api import views

app_name = "expenses"


router = BaseRouter(trailing_slash=False)
router.register("expenses_type", views.ExpensesTypeViewSet, basename="expenses")
router.register("income_type", views.IncomeTypeViewSet, basename="income_type")
router.register(
    "financial_reports", views.FinancialReportViewSet, basename="financial_reports"
)


urlpatterns = [
    path(
        "expenses_type/<int:pk>/children",
        views.ExpensesChildListView.as_view(),
        name="expenses_list_child",
    ),
    path(
        "income_type/<int:pk>/children",
        views.IncomeTypeChildListView.as_view(),
        name="income_list_child",
    ),
    path(
        "income_type/totals/",
        views.FinancialReportIncomeTotalsView.as_view({"get": "list"}),
        name="income-type-totals",
    ),
    path(
        "expenses_type/totals/",
        views.FinancialReportExpenseTotalsView.as_view({"get": "list"}),
        name="expense-type-totals",
    ),
]

urlpatterns += router.urls
