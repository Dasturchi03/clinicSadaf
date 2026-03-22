from django.urls import path

from apps.core.api.router import BaseRouter
from apps.work.api import views 

app_name = 'work'

router = BaseRouter(trailing_slash=False)
router.register("works", views.WorkViewSet, basename="works")

urlpatterns = router.urls + [
    path("mobile/services", views.MobileWorkListView.as_view(), name="mobile_services"),
    path("mobile/services/<int:pk>", views.MobileWorkDetailView.as_view(), name="mobile_service_detail"),
]
