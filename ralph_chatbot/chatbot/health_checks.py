# Add to chatbot/health_check.py

from django.http import HttpResponse
from django.db import connections
from django.db.utils import OperationalError
from redis import Redis
from redis.exceptions import RedisError

def check_database():
    try:
        connections['default'].cursor()
        return True
    except OperationalError:
        return False

def check_redis():
    try:
        redis_client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            socket_timeout=2
        )
        return redis_client.ping()
    except RedisError:
        return False

def check_model_loaded():
    try:
        from .chatbot.model import model
        return model is not None
    except:
        return False

def health_check(request):
    checks = {
        'database': check_database(),
        'redis': check_redis(),
        'model': check_model_loaded()
    }
    
    if all(checks.values()):
        return HttpResponse("healthy", status=200)
    return HttpResponse("unhealthy", status=503)

def readiness_check(request):
    return HttpResponse("ready", status=200)

# Add to chatbot/urls.py
urlpatterns += [
    path('health/', health_check, name='health_check'),
    path('ready/', readiness_check, name='readiness_check'),
]