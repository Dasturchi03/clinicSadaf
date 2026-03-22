from django.urls import path

from apps.core.api.router import BaseRouter
from apps.reservation.api.requests.views import (
    MobileReservationRequestCancelView,
    MobileReservationRequestDetailView,
    MobileReservationRequestListCreateView,
    ReservationRequestViewSet,
)
from apps.reservation.api.reservations.views import (
    MobileMyReservationDetailView,
    MobileMyReservationListView,
    MobileReservationDoctorDetailView,
    MobileReservationDoctorsView,
    MobileReservationDoctorSlotsView,
    ReservationListView,
    ReservationViewSet,
    ReservationDoctorsView,
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
    path("reservation/doctors", ReservationDoctorsView.as_view(), name='doctors_list'),
    path("reservation/doctors/<int:pk>", ReservationDoctorsView.as_view(), name='doctor_detail'),
    path("mobile/reservation/doctors", MobileReservationDoctorsView.as_view(), name="mobile_doctors_list"),
    path("mobile/reservation/doctors/<int:pk>", MobileReservationDoctorDetailView.as_view(), name="mobile_doctor_detail"),
    path("mobile/reservation/doctors/<int:pk>/slots", MobileReservationDoctorSlotsView.as_view(), name="mobile_doctor_slots"),
    path("mobile/reservations", MobileMyReservationListView.as_view(), name="mobile_my_reservations"),
    path("mobile/reservations/<int:pk>", MobileMyReservationDetailView.as_view(), name="mobile_my_reservation_detail"),
    path("mobile/reservation-requests", MobileReservationRequestListCreateView.as_view(), name="mobile_reservation_requests"),
    path("mobile/reservation-requests/<int:pk>", MobileReservationRequestDetailView.as_view(), name="mobile_reservation_request_detail"),
    path("mobile/reservation-requests/<int:pk>/cancel", MobileReservationRequestCancelView.as_view(), name="mobile_reservation_request_cancel"),
    path("reservation/<str:username>/", index),
]

urlpatterns += router.urls
