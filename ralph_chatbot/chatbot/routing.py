from django.urls import re_path
from .consumers import RalphMetricsConsumer

websocket_urlpatterns = [
    re_path(r'^ws/chat/$', RalphMetricsConsumer.as_asgi()),
]
