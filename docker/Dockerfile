# ─── Base Stage ──────────────────────────────────────────
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# ─── Dependencies Stage ─────────────────────────────────
FROM base AS deps

COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/prod.txt

# ─── Production Stage ───────────────────────────────────
FROM base AS production

COPY --from=deps /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

COPY . .

RUN adduser --disabled-password --no-create-home appuser
USER appuser

COPY docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 8000

CMD ["gunicorn", "core.asgi:application", \
     "--bind", "0.0.0.0:8000", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--worker-tmp-dir", "/dev/shm", \
     "--timeout", "120"]
