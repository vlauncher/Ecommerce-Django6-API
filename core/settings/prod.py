from .base import *  # noqa: F401, F403

DEBUG = False

# PostgreSQL for production
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),  # noqa: F405
        "USER": config("DB_USER"),  # noqa: F405
        "PASSWORD": config("DB_PASSWORD"),  # noqa: F405
        "HOST": config("DB_HOST", default="db"),  # noqa: F405
        "PORT": config("DB_PORT", default="5432"),  # noqa: F405
        "CONN_MAX_AGE": 600,
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}

# Security hardening
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)  # noqa: F405
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# WhiteNoise for static files
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Production logging — emit JSON for structured log aggregation
LOGGING["handlers"]["console"]["formatter"] = "verbose"  # noqa: F405
LOGGING["root"]["level"] = "WARNING"  # noqa: F405
