import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-xy59e%t_5$pw!tc@tkx++lq+96r94!#$x7nikaqjhg@kgb1_6g"

DEBUG = True

ALLOWED_HOSTS = ["*"]

AUTH_USER_MODEL = "user.User"

INTERNAL_IPS = ["127.0.0.1"]

INSTALLED_APPS = [
    "corsheaders",
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "django_celery_beat",
    "uvicorn",
    "channels",
    "debug_toolbar",
    "drf_spectacular",
    "apps.notifications",
    "apps.user",
    "apps.core",
    "apps.client",
    "apps.task",
    "apps.medcard",
    "apps.work",
    "apps.specialization",
    "apps.category",
    "apps.disease",
    "apps.credit",
    "apps.transaction",
    "apps.expenses",
    "apps.storage",
    "apps.reservation",
    "apps.report",
    "apps.sms",
]

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "clinicSADAF.urls"

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

WSGI_APPLICATION = "clinicSADAF.wsgi.application"

ASGI_APPLICATION = "clinicSADAF.asgi.application"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "cache_sms",
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("localhost", 6379)],
        },
    },
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "sadaf",
        "USER": "admin",
        "PASSWORD": "admin",
        "HOST": "localhost",
        "PORT": "5433",
        "ATOMIC_REQUESTS": True,
    }
}

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql_psycopg2",
#         "NAME": "sadaf_db",
#         "USER": "postgres",
#         "PASSWORD": "22302621",
#         "HOST": "127.0.0.1",
#         "PORT": "5432",
#         "ATOMIC_REQUESTS": True,
#     }
# }

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': 'sadaf_db',
#         'USER': 'sadaf_db_user',
#         'PASSWORD': '5E9CYWPm779u',
#         'HOST': '127.0.0.1',
#         'PORT': '5433',
#         'ATOMIC_REQUESTS': True
#     }
# }

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

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_SCHEMA_CLASS": "apps.core.schema.CustomAutoSchema",
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
    ),
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
    "DATETIME_FORMAT": "%d-%m-%YT%H:%M",
    "TIME_FORMAT": "%H:%M",
    "DATE_FORMAT": "%d-%m-%Y",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "SADAF API",
    "DESCRIPTION": "SADAF Development",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "DISABLE_ERRORS_AND_WARNINGS": True,
    "SWAGGER_UI_DIST": "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.11.7",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
}

TIME_ZONE = "Asia/Tashkent"

USE_I18N = True
USE_L10N = True

USE_TZ = False
LANGUAGES = (("en", "English"), ("uz", "Uzbek"), ("ru", "Russian"))
LOCALE_PATHS = [
    BASE_DIR / "locale",
]

# Static files (CSS, JavaScript, Images)

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "uploads")

# Default primary key field type

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# SERVER SETTINGS

CORS_ALLOW_ALL_ORIGINS = True
USE_X_FORWARDED_HOST = True
CSRF_TRUSTED_ORIGINS = ["https://api.sadaf-clinic.uz"]

# ESKIZ

ESKIZ_EMAIL = "ulug2203@mail.ru"
ESKIZ_PASSWORD = "Yt$!DIMjOS6hBTP&"
ESKIZ_KEY = "H3NOnP2ZPaNA7kkWNR6JhSLuquoMGU1nl8EaSujf"

# PATTERNS
PHONE_PATTERN = r"^\+\d{12}$"


# celery
CELERY_BROKER_URL = "redis://127.0.0.1:6379"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TIMEZONE = "Asia/Tashkent"
