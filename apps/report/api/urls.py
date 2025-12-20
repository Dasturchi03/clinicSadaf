from django.urls import path
from apps.core.api.router import DefaultRouter
from apps.report.api import views


app_name = "report"


router = DefaultRouter(trailing_slash=False)
router.register("medical_card_report", views.MedicalCardReportViewSet, basename="medical_card_report")


urlpatterns = router.urls

