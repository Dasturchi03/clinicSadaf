from django.urls import path
from apps.notifications.api import views

app_name = 'notifications'


urlpatterns = [
    path("notifications/<str:username>/", views.notification_view, name="room"),
    path("mobile/notifications", views.MobileNotificationListView.as_view(), name="mobile_notifications"),
    path("mobile/notifications/unread-count", views.MobileNotificationUnreadCountView.as_view(), name="mobile_notifications_unread_count"),
    path("mobile/notifications/<int:pk>/read", views.MobileNotificationReadView.as_view(), name="mobile_notifications_read"),
    path("mobile/notifications/read-all", views.MobileNotificationReadAllView.as_view(), name="mobile_notifications_read_all"),
    path("mobile/notifications/devices/register", views.MobileNotificationDeviceRegisterView.as_view(), name="mobile_notifications_device_register"),
    path("mobile/notifications/devices/unregister", views.MobileNotificationDeviceUnregisterView.as_view(), name="mobile_notifications_device_unregister"),
]
