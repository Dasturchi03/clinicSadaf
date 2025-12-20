from rest_framework import serializers

from apps.notifications.models import Notification
from apps.reservation.api.reservations.serializers import ReservationSerializer
from apps.user.api.nested_serializers import NestedDoctorSerializer


class NotificationSerializer(serializers.ModelSerializer):
    notification_receiver = NestedDoctorSerializer(read_only=True)
    notification_reservation = ReservationSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = [
            "notification_id",
            "notification_receiver",
            "notification_reservation",
            "notification_message",
            "created_at",
        ]
