from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.notifications.api.serializers import MobileNotificationSerializer
from apps.notifications.models import Notification
from apps.core.pagination import BasePagination


def notification_view(request, username):
    return render(request, 'notification/index.html', {"username": username})


@extend_schema(tags=["mobile_notifications"])
class MobileNotificationListView(generics.ListAPIView):
    serializer_class = MobileNotificationSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = BasePagination

    def get_queryset(self):
        return Notification.objects.filter(
            notification_receiver=self.request.user
        ).select_related(
            "notification_reservation",
            "notification_reservation__reservation_doctor",
            "notification_reservation__reservation_work",
            "notification_reservation__reservation_client",
        ).order_by("-created_at")


@extend_schema(tags=["mobile_notifications"])
class MobileNotificationUnreadCountView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        unread_count = Notification.objects.filter(
            notification_receiver=request.user,
            is_read=False,
        ).count()
        return Response({"unread_count": unread_count}, status=status.HTTP_200_OK)


@extend_schema(tags=["mobile_notifications"])
class MobileNotificationReadView(generics.UpdateAPIView):
    serializer_class = MobileNotificationSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ["patch"]

    def get_queryset(self):
        return Notification.objects.filter(notification_receiver=self.request.user)

    def patch(self, request, *args, **kwargs):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        serializer = self.get_serializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["mobile_notifications"])
class MobileNotificationReadAllView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def patch(self, request, *args, **kwargs):
        updated_count = Notification.objects.filter(
            notification_receiver=request.user,
            is_read=False,
        ).update(is_read=True)
        return Response({"updated_count": updated_count}, status=status.HTTP_200_OK)
