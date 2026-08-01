FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies and install
COPY requirements/ /app/requirements/
RUN pip install --no-cache-dir -r requirements/prod.txt

# Copy project files
COPY . /app/

# Expose Django app port
EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "core.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
