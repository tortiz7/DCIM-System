import os
from django.core.wsgi import get_wsgi_application
import signal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot.settings')
application = get_wsgi_application()

def handle_shutdown(signum, frame):
    # Clean up model resources
    from chatbot.model import cleanup
    cleanup()

signal.signal(signal.SIGTERM, handle_shutdown)