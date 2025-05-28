"""
Development settings for rental aggregator project.
"""

from .base import *

DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-key-for-local-development-only')

# CORS settings for local development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Email settings - console backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Set server host for Replit compatibility
ALLOWED_HOSTS = ['0.0.0.0', 'localhost', '127.0.0.1', '.replit.dev', '.repl.co', '.replit.app', '*']

# CSRF trusted origins for Replit compatibility
CSRF_TRUSTED_ORIGINS = ['https://*.replit.dev', 'https://*.repl.co', 'https://*.replit.app']

# Additional development apps
INSTALLED_APPS += [
    'django_extensions',
]

# WebSocket settings for Replit environment
USE_TLS = True
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Static files configuration for Daphne
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

ASGI_APPLICATION = 'core.asgi:application'

# Channel layers for Django Channels
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
        },
    },
}

# WebSocket settings for secure connections
SECURE_WEBSOCKET = True
WEBSOCKET_URL = f"wss://{ALLOWED_HOSTS[0] if ALLOWED_HOSTS[0] != '*' else 'localhost'}"