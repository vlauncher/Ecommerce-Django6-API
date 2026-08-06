import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django_application = get_asgi_application()

try:
    from channels.routing import ProtocolTypeRouter, URLRouter
    from apps.interactions.middleware import JWTWebSocketMiddleware
    from apps.interactions.routing import websocket_urlpatterns

    application = ProtocolTypeRouter({
        "http": django_application,
        "websocket": JWTWebSocketMiddleware(URLRouter(websocket_urlpatterns)),
    })
except ImportError:
    application = django_application
