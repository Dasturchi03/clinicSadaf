from django.urls import path

from apps.about.api import views
from apps.core.api.router import BaseRouter


app_name = "about"


router = BaseRouter(trailing_slash=False)
router.register("mobile/articles", views.ArticlePublicViewSet, basename="mobile-articles")
router.register("mobile/news", views.NewsPublicViewSet, basename="mobile-news")


urlpatterns = router.urls + [
    path("mobile/about", views.MobileAboutView.as_view(), name="mobile_about"),
]
