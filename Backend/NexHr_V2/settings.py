"""
Django settings for NexHr_V2 project.
"""

from __future__ import annotations

import os
import sys
from datetime import timedelta
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None

try:
    from corsheaders.defaults import default_headers
except ImportError:  # pragma: no cover - installed via requirements
    default_headers = ()

BASE_DIR = Path(__file__).resolve().parent.parent

if load_dotenv is not None:
    load_dotenv(BASE_DIR / '.env', override=True)


def env_bool(name: str, default: str = 'False') -> bool:
    """Parse a boolean environment variable."""
    return os.getenv(name, default).lower() in ('true', '1', 'yes')


def env_list(name: str, default: str = '') -> list[str]:
    """Parse a comma-separated environment variable into a list."""
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(',') if item.strip()]


SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me-in-production')
DEBUG = env_bool('DEBUG', 'True')

ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver')

APPEND_SLASH = False

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'apps.core',
    'apps.authentication',
    'apps.organization',
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

ROOT_URLCONF = 'NexHr_V2.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'NexHr_V2.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.getenv('DB_NAME', 'NexHr_V2'),
        'USER': os.getenv('DB_USER', 'NexHRMS'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'NexHRMS'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

AUTH_USER_MODEL = 'authentication.User'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 9},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.getenv('TIME_ZONE', 'Asia/Kolkata')
APP_TIMEZONE = os.getenv('APP_TIMEZONE', TIME_ZONE)
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

IS_TESTING = 'test' in sys.argv or env_bool('NEXHR_TESTING', 'False')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'apps.authentication.authentication.SessionJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': os.getenv('API_ANON_THROTTLE', '120/minute'),
        'user': os.getenv('API_USER_THROTTLE', '600/minute'),
        'auth_anon': os.getenv('AUTH_ANON_THROTTLE', '20/minute'),
        'auth_user': os.getenv('AUTH_USER_THROTTLE', '60/minute'),
    },
    'EXCEPTION_HANDLER': 'apps.core.exceptions_handler.custom_exception_handler',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(hours=8),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

AUTH_MAX_LOGIN_ATTEMPTS = int(os.getenv('AUTH_MAX_LOGIN_ATTEMPTS', '5'))
AUTH_LOCKOUT_WINDOW_MINUTES = int(os.getenv('AUTH_LOCKOUT_WINDOW_MINUTES', '15'))
AUTH_LOCKOUT_DURATION_MINUTES = int(os.getenv('AUTH_LOCKOUT_DURATION_MINUTES', '15'))
AUTH_ACCOUNT_LOCK_MIN_IPS = int(os.getenv('AUTH_ACCOUNT_LOCK_MIN_IPS', '2'))
AUTH_EMAIL_VERIFICATION_HOURS = int(os.getenv('AUTH_EMAIL_VERIFICATION_HOURS', '24'))
AUTH_PASSWORD_RESET_HOURS = int(os.getenv('AUTH_PASSWORD_RESET_HOURS', '1'))

FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:4200')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@nexhr.local')
EMAIL_BACKEND = os.getenv(
    'EMAIL_BACKEND',
    'django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', 'True')
EMAIL_USE_SSL = env_bool('EMAIL_USE_SSL', 'False')
EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', '30'))
EMAIL_FAIL_SILENTLY = env_bool('EMAIL_FAIL_SILENTLY', 'False')

CORS_ALLOWED_ORIGINS = env_list(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:5173,http://127.0.0.1:5173',
)
CORS_ALLOW_CREDENTIALS = env_bool('CORS_ALLOW_CREDENTIALS', 'True')
if default_headers:
    CORS_ALLOW_HEADERS = (*default_headers, 'x-branch-id')
