import os
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['nishadparty.org', 'www.nishadparty.org', os.getenv('ALLOWED_HOST', '')]

# Security Settings
SECURE_SSL_REDIRECT = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# Email Configuration
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
DEFAULT_FROM_EMAIL = 'noreply@nishadparty.org'

# Static Files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "https://nishadparty.org",
    "https://www.nishadparty.org",
]
CORS_ALLOW_CREDENTIALS = True

# Sentry Configuration
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

if os.getenv('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=True
    )

# Logging - Override for production
LOGGING['handlers']['file']['filename'] = '/var/log/nishadparty/django.log'
LOGGING['loggers']['django']['level'] = 'WARNING'