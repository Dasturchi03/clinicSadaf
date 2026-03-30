from rest_framework import serializers

from apps.notifications.models import (
    Notification,
    NotificationDevice,
    NotificationDevicePlatforms,
)
from apps.notifications.utils import get_notification_label
from apps.user.api.nested_serializers import NestedDoctorSerializer


class NotificationSerializer(serializers.ModelSerializer):
    notification_receiver = NestedDoctorSerializer(read_only=True)
    notification_reservation = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "notification_id",
            "notification_receiver",
            "notification_reservation",
            "notification_type",
            "notification_message",
            "is_read",
            "created_at",
        ]

    def get_notification_reservation(self, obj):
        if not obj.notification_reservation:
            return None
        reservation = obj.notification_reservation
        return {
            "reservation_id": reservation.reservation_id,
            "reservation_date": reservation.reservation_date.strftime("%d-%m-%Y"),
            "reservation_start_time": reservation.reservation_start_time.strftime("%H:%M"),
            "reservation_end_time": reservation.reservation_end_time.strftime("%H:%M"),
            "cancelled": reservation.cancelled,
        }


class MobileNotificationSerializer(serializers.ModelSerializer):
    notification_reservation = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    next_action = serializers.SerializerMethodField()
    payload = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "notification_id",
            "notification_type",
            "notification_message",
            "notification_reservation",
            "is_read",
            "status_label",
            "next_action",
            "payload",
            "created_at",
        ]

    def get_notification_reservation(self, obj):
        if not obj.notification_reservation:
            return None
        reservation = obj.notification_reservation
        return {
            "reservation_id": reservation.reservation_id,
            "reservation_date": reservation.reservation_date.strftime("%d-%m-%Y"),
            "reservation_start_time": reservation.reservation_start_time.strftime("%H:%M"),
            "reservation_end_time": reservation.reservation_end_time.strftime("%H:%M"),
        }

    def get_status_label(self, obj):
        return get_notification_label(obj.notification_type)

    def get_next_action(self, obj):
        if obj.notification_reservation:
            return "open_reservation"
        return "open_notifications"

    def get_payload(self, obj):
        reservation = obj.notification_reservation
        if not reservation:
            return {
                "target_type": "notification",
                "target_id": obj.notification_id,
            }

        doctor = reservation.reservation_doctor
        work = reservation.reservation_work
        client = reservation.reservation_client
        return {
            "target_type": "reservation",
            "target_id": reservation.reservation_id,
            "doctor": {
                "id": doctor.id,
                "full_name": doctor.full_name(),
            } if doctor else None,
            "service": {
                "work_id": work.work_id,
                "title": work.work_title,
                "price": work.work_basic_price,
            } if work else None,
            "client": {
                "client_id": client.client_id,
                "full_name": f"{client.client_firstname} {client.client_lastname}".strip(),
            } if client else None,
            "reservation_date": reservation.reservation_date.strftime("%d-%m-%Y"),
            "reservation_start_time": reservation.reservation_start_time.strftime("%H:%M"),
            "reservation_end_time": reservation.reservation_end_time.strftime("%H:%M"),
            "cancelled": reservation.cancelled,
        }


class MobileNotificationDeviceSerializer(serializers.ModelSerializer):
    platform = serializers.ChoiceField(
        choices=NotificationDevicePlatforms.choices,
        required=False,
        default=NotificationDevicePlatforms.UNKNOWN,
    )

    class Meta:
        model = NotificationDevice
        fields = [
            "device_id",
            "token",
            "platform",
            "device_uid",
            "is_active",
            "last_seen_at",
        ]
        read_only_fields = ["device_id", "is_active", "last_seen_at"]


class MobileNotificationDeviceUnregisterSerializer(serializers.Serializer):
    token = serializers.CharField()
