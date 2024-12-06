from django.urls import re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from . import consumers

application = ProtocolTypeRouter({
    'websocket': URLRouter([
        re_path(r'ws/chat/$', consumers.ChatConsumer.as_asgi()),
    ]),
})