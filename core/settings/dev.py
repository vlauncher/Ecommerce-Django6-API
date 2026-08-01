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

# Development email backend (prints email content to console)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Development tasks backend (runs tasks immediately synchronously)
TASKS = {
    "default": {
        "BACKEND": "django_tasks.backends.immediate.ImmediateBackend",
        "QUEUES": ["default", "emails"],
    },
}
