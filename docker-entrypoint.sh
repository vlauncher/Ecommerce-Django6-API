#!/bin/sh
set -e

if [ "$DB_HOST" ]; then
    echo "Waiting for PostgreSQL ($DB_HOST:$DB_PORT)..."
    while ! nc -z "$DB_HOST" "$DB_PORT"; do
      sleep 0.5
    done
    echo "PostgreSQL is ready!"
fi

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || true

exec "$@"
