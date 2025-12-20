from django.urls import path
from apps.credit.api import views


app_name = 'credit'


urlpatterns = [
    path("credits/<int:client_id>/list", views.CreditViewSet.as_view({"get": "list", })),
    path("credits/<int:credit_id>/", views.CreditViewSet.as_view({"get": "retrieve", "delete": "destroy", "patch": "partial_update", "put": "update"})),
]
