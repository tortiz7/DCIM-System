import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'your-secret-key-here')
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
ALB_DOMAIN = os.getenv('ALB_DOMAIN', '')
if ALB_DOMAIN and ALB_DOMAIN not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(ALB_DOMAIN)

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

REDIS_HOST = os.getenv('REDIS_HOST', '')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))

REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
        },
    },
}

MODEL_BASE_PATH = os.getenv('MODEL_PATH', str(BASE_DIR / 'chatbot/model'))
MODEL_ADAPTERS_PATH = os.getenv('LORA_PATH', str(BASE_DIR / 'chatbot/model/adapters'))
MODEL_PATH = {
    'base_path': MODEL_BASE_PATH,
    'adapters_path': MODEL_ADAPTERS_PATH
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
    }
}

RALPH_API_URL = os.getenv('RALPH_API_URL', 'http://localhost:8000/api')
RALPH_API_TOKEN = os.getenv('RALPH_API_TOKEN', '')

PROMETHEUS_METRICS_EXPORT_PORT = 9100
PROMETHEUS_METRICS_EXPORT_ADDRESS = ''

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
