from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]

urlpatterns += i18n_patterns(
    path("", include("apps.user.api.urls", namespace="user")),
    path("", include("apps.client.api.urls", namespace="client")),
    path("task/", include("apps.task.urls", namespace="task")),
    path("", include("apps.medcard.api.urls", namespace="medcard")),
    path("", include("apps.work.api.urls", namespace="work")),
    path("", include("apps.specialization.api.urls", namespace="specialization")),
    path("", include("apps.category.api.urls", namespace="category")),
    path("", include("apps.disease.api.urls", namespace="disease")),
    path("", include("apps.notifications.api.urls", namespace="notifications")),
    path("", include("apps.credit.api.urls", namespace="credit")),
    path("", include("apps.transaction.api.urls", namespace="transaction")),
    path("", include("apps.expenses.api.urls", namespace="expenses")),
    path("", include("apps.storage.api.urls", namespace="storage")),
    path("", include("apps.reservation.api.urls", namespace="reservation")),
    path("", include("apps.report.api.urls", namespace="report")),
    path("", include("apps.sms.api.urls", namespace="sms")),
    path("", include("apps.about.api.urls", namespace="about")),
    prefix_default_language=False,
)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
