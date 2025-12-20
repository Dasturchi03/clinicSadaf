from apps.core.api.router import BaseRouter
from apps.sms.api import views


app_name = "sms"


router = BaseRouter(trailing_slash=False)
router.register("sms", views.SMSView, basename="sms")

urlpatterns = router.urls
