from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/reservation_(?P<username>\w+)/$", consumers.ReservationConsumer.as_asgi()),
]
