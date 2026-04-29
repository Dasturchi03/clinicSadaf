from django.urls import path, include
from apps.core.api.router import BaseRouter
from apps.vacancies.api import views


app_name = "vacancies"

router = BaseRouter(trailing_slash=False)
router.register("vacancies", views.VacancyViewSet, basename="vacancies")
router.register("vacancy-applications", views.VacancyApplicationViewSet, basename="vacancy-applications")


mobile_router = BaseRouter(trailing_slash=False)
mobile_router.register("vacancies", views.VacancyPublicViewSet, basename="mobile-vacancies")


urlpatterns = router.urls + [
    path(
        "mobile/vacancies/apply",
        views.VacancyApplicationCreateView.as_view(),
        name="mobile-vacancy-apply",
    ),

    path(
        "mobile/",
        include(mobile_router.urls),
    ),

    path(
        "vacancy-applications/<int:pk>/status",
        views.VacancyApplicationStatusUpdateView.as_view(),
        name="vacancy-application-status",
    ),
]
