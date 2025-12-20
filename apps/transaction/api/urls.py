from django.urls import path

from apps.transaction.api import views

app_name = "transaction"


urlpatterns = [
    path(
        "transactions",
        views.TransactionViewSet.as_view({"get": "list"}),
        name="transactions",
    ),
    path(
        "transactions/<str:pk>/",
        views.TransactionViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "put": "update",
                "delete": "destroy",
            }
        ),
    ),
    path(
        "transactions/credits",
        views.TransactionViewSet.as_view({"post": "credits_pay"}),
    ),
    path(
        "transactions/clients_balance",
        views.TransactionViewSet.as_view({"post": "clients_balance"}),
    ),
    path(
        "transactions/clients_balance/update/<str:pk>/",
        views.TransactionViewSet.as_view({"patch": "update_client_balance"}),
    ),
    path(
        "transactions/clients_refund",
        views.TransactionViewSet.as_view({"post": "clients_refund"}),
    ),
    path(
        "transactions/client_balance_transfer",
        views.TransactionViewSet.as_view({"post": "client_balance_transfer"}),
        name="client_balance_transfer",
    ),
    path(
        "transactions/credits_all",
        views.TransactionViewSet.as_view({"post": "credits_pay_all"}),
        name="credits_pay_all",
    ),
    path(
        "transactions/card_pay",
        views.TransactionViewSet.as_view({"post": "medical_card_pay_all"}),
        name="medical_card_pay_all",
    ),
    path(
        "transactions/card_credit",
        views.TransactionViewSet.as_view({"post": "medical_card_credit_all"}),
        name="medical_card_credit_all",
    ),
]
