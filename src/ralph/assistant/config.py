# src/ralph/assistant/config.py
from django.conf import settings

CHATBOT_URL = getattr(settings, 'CHATBOT_URL', 'http://chatbot:8001')
CHATBOT_WS_URL = getattr(settings, 'CHATBOT_WS_URL', 'ws://chatbot:8001/ws/')