from django.apps import AppConfig


class ReservationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.reservation'

    def ready(self):
        from . import signals