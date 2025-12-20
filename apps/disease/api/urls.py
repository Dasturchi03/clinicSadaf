from django.urls import path

from apps.core.api.router import BaseRouter
from apps.disease.api import views


app_name = 'disease'


router = BaseRouter(trailing_slash=False)
router.register("diseases", views.DiseaseViewSet, basename="diseases")


urlpatterns = [
    # Список подболезней
    path('diseases/<int:pk>/children', views.DiseaseChildListView.as_view(), name='disease_list_child'),
]

urlpatterns += router.urls
