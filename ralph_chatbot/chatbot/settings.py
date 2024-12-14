import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'your-secret-key-here')
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
ALB_DOMAIN = os.getenv('ALB_DOMAIN', '')
if ALB_DOMAIN and ALB_DOMAIN not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(ALB_DOMAIN)

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'corsheaders',
    'rest_framework',
    'chatbot',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'chatbot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'chatbot.wsgi.application'
ASGI_APPLICATION = 'chatbot.asgi.application'

# Redis Configuration for Docker
REDIS_HOST = 'redis'  # This matches the service name in docker-compose
REDIS_PORT = 6379

# Channel Layers (for WebSocket)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis", 6379)],  # Docker service name
        },
    },
}

# CORS Configuration
CORS_ALLOW_ALL_ORIGINS = True

# Model Configuration
MODEL_BASE_PATH = os.getenv('MODEL_PATH', str(BASE_DIR / 'chatbot/model'))
MODEL_ADAPTERS_PATH = os.getenv('LORA_PATH', str(BASE_DIR / 'chatbot/model/adapters'))
MODEL_PATH = {
    'base_path': MODEL_BASE_PATH,
    'adapters_path': MODEL_ADAPTERS_PATH
}

# Mock asset metrics (used for demo purposes instead of Ralph API)
MOCK_ASSET_METRICS = {
    'assets': {
        'total_count': 120,  # Example number of assets
        'status_summary': 'All systems operational'
    }
}

# Static files Configuration
STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/static'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'chatbot': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
