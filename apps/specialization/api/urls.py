from apps.core.api.router import BaseRouter
from apps.specialization.api import views


app_name = 'specialization'


router = BaseRouter(trailing_slash=False)
router.register("specializations", views.SpecializationViewSet, basename="specializations")

urlpatterns = router.urls

