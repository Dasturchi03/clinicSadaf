from channels.db import database_sync_to_async
from .models import Reservation
from datetime import date


@database_sync_to_async
def filter_reservation():
    current_date = date.today()
    queryset = Reservation.objects.filter(reservation_date=current_date)
    
    list_reservations = [
        {
            "reservation_id": instance.reservation_id,
            "reservation_client": instance.reservation_client.client_id,
            "reservation_doctor": instance.reservation_doctor.id,
            "reservation_notes": instance.reservation_notes,
            "reservation_date": instance.reservation_date.strftime("%d-%m-%Y"),
            "reservation_start_time": instance.reservation_start_time.strftime("%H:%M"),
            "reservation_end_time": instance.reservation_end_time.strftime("%H:%M"),
            "cancelled": instance.cancelled,
            "created_at": instance.created_at.strftime("%d-%m-%YT%H:%M"),
        }
        for instance in queryset
    ]
    return list_reservations