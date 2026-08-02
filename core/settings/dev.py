from .base import *  # noqa: F401, F403

DEBUG = True

# SQLite for local development
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}

# Use LocMemCache for development if Redis is not running locally
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}



# Relax CORS for development
CORS_ALLOW_ALL_ORIGINS = True

# Use Immediate backend for tasks (synchronous in dev)
TASKS = {
    "default": {
        "BACKEND": "django.tasks.backends.ImmediateBackend",
    },
}
