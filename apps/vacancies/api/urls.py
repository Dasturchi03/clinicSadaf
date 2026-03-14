from django.urls import path
from apps.core.api.router import BaseRouter
from apps.vacancies.api import views


app_name = "vacancies"

router = BaseRouter(trailing_slash=False)
router.register("vacancies", views.VacancyViewSet, basename="vacancies")
router.register("vacancy-applications", views.VacancyApplicationViewSet, basename="vacancy-applications")
router.register("mobile/vacancies", views.VacancyPublicListViewSet, basename="mobile-vacancies")

urlpatterns = router.urls + [
    path(
        "mobile/vacancies/apply",
        views.VacancyApplicationCreateView.as_view(),
        name="mobile-vacancy-apply",
    ),
    path(
        "vacancy-applications/<int:pk>/status",
        views.VacancyApplicationStatusUpdateView.as_view(),
        name="vacancy-application-status",
    ),
]
