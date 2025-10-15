import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Environment: 'development' or 'production'
ENVIRONMENT = os.environ.get('DJANGO_ENV', 'development')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', "django-insecure-g3szm*j^#hd#zcg&av5l2v^w#ms3)tiuzt1ldmon7ntwxe8()b")

# Debug mode based on environment
DEBUG = ENVIRONMENT == 'development'

# Allowed hosts
ALLOWED_HOSTS = ['*', 'nishadparty.org', 'www.nishadparty.org', 'localhost', '127.0.0.1']

# CSRF Settings
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8020",
    "http://127.0.0.1:8020",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://nishadparty.org",
    "http://nishadparty.org",
    "https://www.nishadparty.org",
    "http://www.nishadparty.org"
]

CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False

# CORS Settings
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'django_extensions',
]

LOCAL_APPS = [
    'accounts',
    'membership',
    'donations',
    'campaigns',
    'assets',
    'meetings',
    'analytics',
    'communications',
    'community',
    'content',
    'core',
    'gatepass',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    "django.middleware.security.SecurityMiddleware",
    'whitenoise.middleware.WhiteNoiseMiddleware',
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "nishadparty.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "nishadparty.wsgi.application"

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'nishadpartyprod',
        'USER': 'nishadparty_user',
        'PASSWORD': 'nishadpartydbprod',
        'HOST': '45.159.230.101',
        'PORT': '6546',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en"
TIME_ZONE = "Asia/Kolkata"

USE_I18N = False
USE_L10N = False
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Static files storage - use WhiteNoise without strict manifest
if ENVIRONMENT == 'production':
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
        },
    }
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

# Third-party API Keys
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')
MSG91_AUTH_KEY = os.environ.get('MSG91_AUTH_KEY')
MSG91_DEFAULT_TEMPLATE = os.environ.get('MSG91_DEFAULT_TEMPLATE')
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

# Email Configuration
if ENVIRONMENT == 'production':
    EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
    DEFAULT_FROM_EMAIL = 'noreply@nishadparty.org'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 hours

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING' if ENVIRONMENT == 'production' else 'INFO',
            'propagate': True,
        },
        'accounts': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'donations': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}


#testing