from django.urls import path

from rest_framework.routers import DefaultRouter
from apps.medcard.api import views

app_name = "medcard"


router = DefaultRouter(trailing_slash=False)
router.register("actions", views.ActionViewset, basename="actions")
router.register("x_ray", views.XrayViewSet, basename="x_ray")


urlpatterns = [
    path(
        "medcards",
        views.MedicalCardViewSet.as_view({"post": "create"}),
        name="medcards_create",
    ),
    path(
        "medcards/<int:client_id>/list",
        views.MedicalCardViewSet.as_view({"get": "list"}),
        name="medcards",
    ),
    path(
        "medcards/<int:pk>",
        views.MedicalCardViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="medcards_instance",
    ),
    path(
        "medcards/all",
        views.MedicalCardListView.as_view({"get": "list"}),
        name="medcard_list",
    ),
    path("medcards/teeth", views.ToothListView.as_view(), name="teeth_list"),
    path("mobile/treatments", views.MobileTreatmentListView.as_view(), name="mobile_treatments"),
    path("mobile/treatments/<int:pk>", views.MobileTreatmentDetailView.as_view(), name="mobile_treatment_detail"),
]

urlpatterns += router.urls
