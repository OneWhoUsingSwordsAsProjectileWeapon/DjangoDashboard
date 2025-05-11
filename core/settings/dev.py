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
