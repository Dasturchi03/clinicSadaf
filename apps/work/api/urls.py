from apps.core.api.router import BaseRouter
from apps.work.api import views 

app_name = 'work'

router = BaseRouter(trailing_slash=False)
router.register("works", views.WorkViewSet, basename="works")

urlpatterns = router.urls
