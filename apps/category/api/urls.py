from apps.category.api import views
from apps.core.api.router import BaseRouter

app_name = "category"

router = BaseRouter(trailing_slash=False)
router.register("categories", views.CategoryViewSet, basename="categories")
router.register(
    "print_out_categories",
    views.PrintOutCategoryViewSet,
    basename="print_out_categories",
)


urlpatterns = router.urls
