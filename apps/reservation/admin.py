from django.contrib import admin
from .models import Reservation


class ReservationAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "reservation_client",
        "reservation_doctor",
        "reservation_date",
        "reservation_start_time",
        "reservation_end_time",
        "created_at",
        "cancelled"
    ]


admin.site.register(Reservation, ReservationAdmin)
