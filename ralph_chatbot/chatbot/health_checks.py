from django.http import HttpResponse
from django.db import connections
from django.db.utils import OperationalError
from redis import Redis
from redis.exceptions import RedisError
from django.conf import settings
import os

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
    model_path = settings.MODEL_PATH['base_path']
    required_files = [
        'tokenizer.json',
        'tokenizer_config.json',
        'special_tokens_map.json',
        'adapters/adapter_config.json',
        'adapters/adapter_model.safetensors'
    ]
    return all(os.path.exists(os.path.join(model_path, f)) for f in required_files)

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
