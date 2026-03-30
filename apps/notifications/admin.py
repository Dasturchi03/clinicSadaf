from django.contrib import admin
from .models import Notification, NotificationDevice

admin.site.register(Notification)
admin.site.register(NotificationDevice)
