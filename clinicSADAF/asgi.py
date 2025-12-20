import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from uvicorn import run

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinicSADAF.settings')

django_asgi_app = get_asgi_application()

from .middleware import TokenAuthMiddleware
from apps.notifications import routing as notifications_routing
from apps.reservation import routing as reservation_routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,

    "websocket": AllowedHostsOriginValidator(
        TokenAuthMiddleware(
            URLRouter(
                notifications_routing.websocket_urlpatterns +
                reservation_routing.websocket_urlpatterns
            )
        )
    ),

})

if __name__ == "__main__":
    run(application, host="127.0.0.1", port=8000)


#  uvicorn clinicSADAF.asgi:application
