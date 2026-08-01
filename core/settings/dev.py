from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ["*", "testserver"]

# Allow all origins in development (Vite, React, Mobile emulators, etc.)
CORS_ALLOW_ALL_ORIGINS = True


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}

# Real Gmail SMTP Email Backend
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "samsonamosv2@gmail.com")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "odjcdtfryrorxjkb")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "VEXSTORE <samsonamosv2@gmail.com>")

# Development tasks backend (runs tasks immediately synchronously)
TASKS = {
    "default": {
        "BACKEND": "django_tasks.backends.immediate.ImmediateBackend",
        "QUEUES": ["default", "emails"],
    },
}

