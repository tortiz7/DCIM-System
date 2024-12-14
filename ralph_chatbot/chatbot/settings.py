import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'your-secret-key-here')
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
ALB_DOMAIN = os.getenv('ALB_DOMAIN', '')
if ALB_DOMAIN and ALB_DOMAIN not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(ALB_DOMAIN)

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
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
    'django.middleware.csrf.CsrfViewMiddleware',
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

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', ''),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Redis Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')  # Default to 'redis' for Docker
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"

# Channel Layers for WebSocket
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(settings.REDIS_HOST, settings.REDIS_PORT)],
            "capacity": 1500,
            "expiry": 60,
            "retry_on_timeout": True,
            "symmetric_encryption_keys": [settings.SECRET_KEY],
        },
    },
}


# Cache Configuration
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{REDIS_URL}/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "RETRY_ON_TIMEOUT": True,
            "MAX_CONNECTIONS": 1000,
            "CONNECTION_POOL_KWARGS": {"max_connections": 100},
        }
    }
}

# Session Configuration
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
SESSION_COOKIE_NAME = 'chatbot_sessionid'
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# CSRF Configuration
CSRF_COOKIE_NAME = 'chatbot_csrftoken'
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_TRUSTED_ORIGINS = ['http://*', 'https://*']  # Adjust in production
CSRF_USE_SESSIONS = True

# CORS Configuration
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8001',
    'http://127.0.0.1:8001',
]
if ALB_DOMAIN:
    CORS_ALLOWED_ORIGINS.append(f'http://{ALB_DOMAIN}')
    CORS_ALLOWED_ORIGINS.append(f'https://{ALB_DOMAIN}')

# Model Configuration
MODEL_BASE_PATH = os.getenv('MODEL_PATH', str(BASE_DIR / 'chatbot/model'))
MODEL_ADAPTERS_PATH = os.getenv('LORA_PATH', str(BASE_DIR / 'chatbot/model/adapters'))
MODEL_PATH = {
    'base_path': MODEL_BASE_PATH,
    'adapters_path': MODEL_ADAPTERS_PATH
}

# Ralph API Configuration
RALPH_API_URL = os.getenv('RALPH_API_URL', 'http://localhost:8000/api')
RALPH_API_TOKEN = os.getenv('RALPH_API_TOKEN', '')

# Prometheus Metrics Configuration
PROMETHEUS_METRICS_EXPORT_PORT = 9100
PROMETHEUS_METRICS_EXPORT_ADDRESS = ''

# Static files Configuration
STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/static'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

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

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'