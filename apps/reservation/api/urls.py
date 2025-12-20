from django.urls import path

from apps.core.api.router import BaseRouter
from apps.reservation.api.requests.views import ReservationRequestViewSet
from apps.reservation.api.reservations.views import (
    ReservationListView,
    ReservationViewSet,
    index,
)

app_name = "reservation"


router = BaseRouter()
router.register(
    "reservation_requests", ReservationRequestViewSet, basename="reservation_requests"
)


urlpatterns = [
    path(
        "reservation/",
        ReservationViewSet.as_view({"post": "create"}),
        name="reservation_create",
    ),
    path("reservation/list", ReservationListView.as_view(), name="reservation_list"),
    path(
        "reservation/<int:reservation_id>/",
        ReservationViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "put": "cancel",
                "delete": "destroy",
            }
        ),
        name="reservation_instance",
    ),
    path(
        "reservation/<int:reservation_id>/force",
        ReservationViewSet.as_view({"patch": "force_update"}),
        name="reservation_instance",
    ),
    path("reservation/<str:username>/", index),
]

urlpatterns += router.urls
