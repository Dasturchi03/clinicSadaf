from apps.about.api import views
from apps.core.api.router import BaseRouter


app_name = "about"


router = BaseRouter(trailing_slash=False)
router.register('articles', views.ArticleViewSet, basename='articles')


urlpatterns = router.urls
