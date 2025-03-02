"""
Django settings for SuperMind project.

Generated by 'django-admin startproject' using Django 4.2.14.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""


# Build paths inside the project like this: BASE_DIR / 'subdir'.
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-2++rk3)2@n!va_n2k^f0nn#1()2f2m-b#ip6bckvd5b^c3ma-0"

# SECURITY WARNING: don't run with debug turned on in production!
import os
from dotenv import load_dotenv
load_dotenv()
DEBUG = os.getenv('DEBUG', 'False') == 'True'


ALLOWED_HOSTS = [
    '127.0.0.1', 
    'localhost', 
    '192.168.0.104',
    'supermind-djb0e9fsfhaabbcx.westindia-01.azurewebsites.net',
    'tragic-christal-supermind-b64b5075.koyeb.app',
    'supermind-9fii.onrender.com'  # Remove https:// prefix
]

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = [
    'https://supermind-9fii.onrender.com',
    'http://supermind-djb0e9fsfhaabbcx.westindia-01.azurewebsites.net',
    'http://tragic-christal-supermind-b64b5075.koyeb.app',
    'http://localhost:8081',
    'http://127.0.0.1:8000',
    'http://192.168.0.104:8000',
    'http://192.168.0.104:8081',
    "exp://localhost:19000",  # Expo development
    "chrome-extension://hcpbkdfipfblmfjeloalfconfjkkhipo"  # Add your extension ID
]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "video_summary",
    'corsheaders',
    'instagram',
    'web',
    'utils',
    'URL_handler',
    'rest_framework',
]

# import sys
# import os
# print(f"PYTHON PATH: {sys.path}")
# print(f"BASE DIR: {BASE_DIR}")
# print(f"INSTALLED APPS: {INSTALLED_APPS}")
# print(f"video_summary path exists: {os.path.exists(os.path.join(BASE_DIR, 'video_summary'))}")


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'SuperMind.middleware.SupabaseAuthMiddleware',
]

# Update CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8081",
    "http://192.168.0.104:8000",
    "http://192.168.0.104:8081",
    "http://192.168.0.104",
    "http://supermind-djb0e9fsfhaabbcx.westindia-01.azurewebsites.net",
    "http://tragic-christal-supermind-b64b5075.koyeb.app",
    "https://supermind-9fii.onrender.com",
    "exp://localhost:19000",  # Expo development
    "chrome-extension://hcpbkdfipfblmfjeloalfconfjkkhipo"  # Add your extension ID
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_ALLOW_ALL_ORIGINS = True  # Temporarily set to True for testing
CORS_ALLOW_CREDENTIALS = True
CORS_EXPOSE_HEADERS = ['Content-Type', 'X-CSRFToken']
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CSRF_COOKIE_SAMESITE = 'Lax'  # or 'None' if needed
CSRF_COOKIE_SECURE = False  # Set to True in production
SESSION_COOKIE_SECURE = False  # Set to True in production


ROOT_URLCONF = "SuperMind.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "SuperMind.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
