from django.urls import path
from apps.core.api.router import BaseRouter
from apps.storage.api import views


app_name = "storage"


router = BaseRouter(trailing_slash=False)
router.register("storage_item", views.StorageItemViewSet, basename="storage_item")


urlpatterns = [
    path('storage_item/not_in_storage/', views.StorageItemsListView.as_view(), name='not_in_storage'),

    path("storage", views.StorageViewSet.as_view({"get": "list", "post": "create"}), name="storage"),
    path("storage/<int:storage_id>/", views.StorageViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"}), name="storage_instance"),
    path("storage/<int:storage_id>/add_quantity", views.StorageViewSet.as_view({"patch": "add_quantity"}), name="add_quantity"),
    path("storage/<int:storage_id>/minus_quantity", views.StorageViewSet.as_view({"patch": "minus_quantity"}), name="minus_quantity"),
    path("storage/<int:storage_id>/give_item", views.StorageViewSet.as_view({"patch": "give_item"}), name="give_item"),

    path("storage_history", views.StorageHistoryViewSet.as_view({"get": "list"}), name="storage_history"),
    path("storage_history/<int:storage_history_id>/", views.StorageHistoryViewSet.as_view({"get": "retrieve"}), name="storage_history_instance"),

]

urlpatterns += router.urls