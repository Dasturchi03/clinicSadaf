from django.urls import path

from apps.client.api import views
from apps.core.api.router import BaseRouter

app_name = "client"


router = BaseRouter(trailing_slash=False)
router.register("clients", views.ClientViewSet, basename="clients")
router.register(
    "client_anamnesis", views.ClientAnamnesisViewSet, basename="client_anamnesis"
)


urlpatterns = [
    path("mobile/dashboard", views.MobileDashboardView.as_view(), name="mobile_dashboard"),
    path("mobile/me", views.MobileMeView.as_view(), name="mobile_me"),
    path("mobile/status", views.MobileStatusView.as_view(), name="mobile_status"),
    path("mobile/loyalty", views.MobileLoyaltyView.as_view(), name="mobile_loyalty"),
    path("mobile/cashback/history", views.MobileCashbackHistoryView.as_view(), name="mobile_cashback_history"),
    path("mobile/referral/apply-code", views.MobileApplyReferralCodeView.as_view(), name="mobile_apply_referral_code"),
    path(
        "clients/create/flutter",
        views.ClientFlutterViewSet.as_view({"post": "create"}),
        name="client_create_flutter",
    ),
    path(
        "clients/update/flutter/<int:pk>/",
        views.ClientFlutterViewSet.as_view(
            {"patch": "partial_update", "get": "retrieve"}
        ),
        name="client_update_flutter",
    ),
    path(
        "clients/merge/<int:pk>/",
        views.MergeClientsView.as_view(),
        name="merge_clients",
    ),
]


urlpatterns += router.urls
