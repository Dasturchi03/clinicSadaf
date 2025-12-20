from django.urls import path
from apps.notifications.api import views

app_name = 'notifications'


urlpatterns = [
    path("notifications/<str:username>/", views.notification_view, name="room"),
]