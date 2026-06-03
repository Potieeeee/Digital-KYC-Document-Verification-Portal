from pathlib import Path
from decouple import config
import dj_database_url
import os
import datetime
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=True, cast=bool)


def _bool_config(name, default):
    raw_value = os.environ.get(name)

    if raw_value is None:
        return default

    try:
        return config(name, default=default, cast=bool)
    except ValueError:
        return default

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1"
).split(",")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "rest_framework_simplejwt",
    "axes",
    "cloudinary",
    "cloudinary_storage",
    "sslserver",

    "accounts",
    "kyc",
    "api",
    "auditlog",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "config.middleware.slash_normalizer.DuplicateSlashMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "axes.middleware.AxesMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "config.context_processors.global_nav",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# Use SQLite by default and fall back to PostgreSQL when DATABASE_URL is provided.

DATABASE_URL = config("DATABASE_URL", default=None)

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


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


LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# Django 4.2+ / 5+ / 6+ storage settings
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


CLOUDINARY_STORAGE = {
    "CLOUD_NAME": config("CLOUDINARY_CLOUD_NAME", default=""),
    "API_KEY": config("CLOUDINARY_API_KEY", default=""),
    "API_SECRET": config("CLOUDINARY_API_SECRET", default=""),
}


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}


AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "accounts.backends.EmailOrUsernameBackend",
    "django.contrib.auth.backends.ModelBackend",
]


AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = datetime.timedelta(minutes=15)
AXES_LOCK_OUT_AT_FAILURE = True
AXES_RESET_ON_SUCCESS = True
# Temporarily disable django-axes so developers can log in while debugging.
# Set to True to re-enable lockouts in production.
AXES_ENABLED = True


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "kyc-ratelimit-cache",
    }
}


# 15-minute rolling session timeout
SESSION_COOKIE_AGE = 900
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True


# Local development security settings
# Use HTTP locally: http://127.0.0.1:8000/
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=False, cast=bool)
SESSION_COOKIE_SECURE = _bool_config("SESSION_COOKIE_SECURE", default=not DEBUG)
CSRF_COOKIE_SECURE = _bool_config("CSRF_COOKIE_SECURE", default=not DEBUG)

# Keep Django's built-in auth redirects aligned with this project's routes.
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/login/"

# Login/logout redirect fix
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/login/"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

CSRF_TRUSTED_ORIGINS = (
    config("CSRF_TRUSTED_ORIGINS", default="").split(",")
    if config("CSRF_TRUSTED_ORIGINS", default="")
    else []
)