import os
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv

# ─── Paths ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ─── Security ───────────────────────────────────────────
SECRET_KEY = config("SECRET_KEY", default="django-insecure-default-key-for-dev-only")
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

# ─── Auth User Model ───────────────────────────────────
AUTH_USER_MODEL = "users.User"

# ─── Application Registry ──────────────────────────────
INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "cloudinary_storage",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    # Third-party
    "corsheaders",
    "django_filters",
    "cloudinary",
    "ninja",
    # Local apps
    "apps.users",
    "apps.shops",
    "apps.catalog",
    "apps.commerce",
    "apps.payments",
    "apps.interactions",
    "apps.management_api",
]

# ─── Middleware ──────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "ninja.compatibility.files.fix_request_files_middleware",
]

# ─── URL Configuration ──────────────────────────────────
ROOT_URLCONF = "core.urls"

# ─── Templates ───────────────────────────────────────────
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.csp",
            ],
        },
    },
]

# ─── WSGI / ASGI ────────────────────────────────────────
WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

# ─── Password Validation ────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ─── Internationalization ───────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ─── Static Files ───────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ─── Default Auto Field ─────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── JWT Settings ────────────────────────────────────────
JWT_SECRET_KEY = SECRET_KEY
JWT_ACCESS_EXPIRATION_MINUTES = 30
JWT_REFRESH_EXPIRATION_DAYS = 7

# ─── Cloudinary ──────────────────────────────────────────
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": config("CLOUDINARY_CLOUD_NAME", default=""),
    "API_KEY": config("CLOUDINARY_API_KEY", default=""),
    "API_SECRET": config("CLOUDINARY_API_SECRET", default=""),
}

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# ─── Email & OTP ────────────────────────────────────────
EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@ecommerce.com")

OTP_EXPIRY_MINUTES = 10
SHOP_INVITATION_EXPIRY_DAYS = config("SHOP_INVITATION_EXPIRY_DAYS", default=7, cast=int)
PAYSTACK_SECRET_KEY = config("PAYSTACK_SECRET_KEY", default="")
PAYSTACK_PUBLIC_KEY = config("PAYSTACK_PUBLIC_KEY", default="")
PLATFORM_COMMISSION_PERCENT = config("PLATFORM_COMMISSION_PERCENT", default=10, cast=int)
SELLER_PAYOUT_HOLD_DAYS = config("SELLER_PAYOUT_HOLD_DAYS", default=7, cast=int)
DISPUTE_WINDOW_DAYS = config("DISPUTE_WINDOW_DAYS", default=7, cast=int)

# ─── Google OAuth ────────────────────────────────────────
GOOGLE_OAUTH_CLIENT_ID = config("GOOGLE_OAUTH_CLIENT_ID", default="")
GOOGLE_OAUTH_CLIENT_SECRET = config("GOOGLE_OAUTH_CLIENT_SECRET", default="")
GOOGLE_OAUTH_REDIRECT_URI = config(
    "GOOGLE_OAUTH_REDIRECT_URI",
    default="http://localhost:8000/api/v1/auth/google/callback/",
)

# ─── CORS ────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000",
    cast=Csv(),
)

# ─── Content Security Policy (Django 6.0) ────────────────
from django.utils.csp import CSP

SECURE_CSP = {
    "default-src": [CSP.SELF],
    "script-src": [CSP.SELF, CSP.NONCE, "https://cdn.jsdelivr.net", "'unsafe-inline'"],
    "style-src": [CSP.SELF, CSP.NONCE, "https://cdn.jsdelivr.net", "'unsafe-inline'"],
    "img-src": [CSP.SELF, "https:"],
    "font-src": [CSP.SELF, "https:", "https://cdn.jsdelivr.net"],
    "object-src": [CSP.NONE],
    "base-uri": [CSP.SELF],
    "frame-ancestors": [CSP.NONE],
    "connect-src": [CSP.SELF, "https://accounts.google.com", "https://oauth2.googleapis.com"],
}

# ─── Caching (Redis) ────────────────────────────────────
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://127.0.0.1:6379/0"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [config("REDIS_URL", default="redis://127.0.0.1:6379/0")]},
    }
}

# ─── Django 6.0 Background Tasks ────────────────────────
TASKS = {
    "default": {
        "BACKEND": "django.tasks.backends.ImmediateBackend",
    },
}

# ─── Logging ─────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": config("DJANGO_LOG_LEVEL", default="INFO"),
            "propagate": False,
        },
    },
}
