from django.urls import re_path, path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<conversation_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
    path('ws/chat/<int:conversation_id>/', consumers.ChatConsumer.as_asgi()),
]