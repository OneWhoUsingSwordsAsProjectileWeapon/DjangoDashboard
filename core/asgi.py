import os
import django
from django.core.asgi import get_asgi_application

# Установка переменной окружения ДО всех импортов
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')

# Инициализация Django
django.setup()  # <- Это критически важно!

# Импорт остальных компонентов ПОСЛЕ django.setup()
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chat.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(chat.routing.websocket_urlpatterns)
    ),
})