import django_filters as filters

from apps.user.models import User
from apps.reservation.models import Reservation


class ReservationFilter(filters.FilterSet):
    cancelled = filters.BooleanFilter(
        field_name="cancelled",
        lookup_expr="exact",
        help_text="Provide True or False argument to get cancelled or not cancelled reservations",
    )
    reservation_date = filters.DateFilter(
        input_formats=["%d-%m-%Y"], field_name="reservation_date", lookup_expr="exact"
    )
    start_date = filters.DateFilter(
        input_formats=["%d-%m-%Y"], field_name="reservation_date", lookup_expr="gte"
    )
    end_date = filters.DateFilter(
        input_formats=["%d-%m-%Y"], field_name="reservation_date", lookup_expr="lte"
    )

    class Meta:
        model = Reservation
        fields = ["reservation_doctor", "reservation_client", "is_initial"]


class ReservationDoctorsFilter(filters.FilterSet):
    reservation_date = filters.DateFilter(
        input_formats=["%d-%m-%Y"], field_name="user_schedule__day", lookup_expr="exact", required=True
    )

    class Meta:
        model = User
        fields = ['reservation_date']
