# 🏪 Django 6 Multi-Vendor E-Commerce Marketplace REST API

A production-grade, multi-vendor e-commerce marketplace REST API built with **Django 6**, **Django REST Framework (DRF)**, **SimpleJWT**, **PostgreSQL**, and **Docker**.

---

## 🛠 Features Overview

- **Authentication & Security**: Custom User model, 6-digit OTP email verification, SimpleJWT Bearer tokens, Google OAuth 2.0.
- **Multi-Vendor Marketplace**: Seller profiles, commission rules, vendor sub-orders, seller payouts.
- **Product Catalog**: Hierarchical categories (`django-treebeard`), Parent/Child Variant SKUs, dynamic attribute engine, media uploads.
- **Verified Product Reviews**: 1–5 star ratings, comments, and community helpful voting.
- **Shopping Cart**: Guest session carts, user carts, cart merging on login, saved items for later.
- **Order Engine**: FSM lifecycle (`DRAFT` → `PENDING_PAYMENT` → `PAID` → `PROCESSING` → `SHIPPED` → `DELIVERED`), point-in-time item snapshots, RMA returns.
- **Payment Gateway Abstraction**: Integrations for **Stripe**, **PayPal**, and **Flutterwave** with idempotency key tracking.
- **Inventory Management**: Concurrency-safe atomic stock reservation (`SELECT FOR UPDATE`), warehouse management, stock movement audit ledger.
- **Shipping**: Geographic zones, flat/weight rates, vendor fulfillment tracking.
- **Promotions**: Coupon discount strategy engine (`PERCENTAGE`, `FIXED_AMOUNT`, `FREE_SHIPPING`), flash sales, quantity tier pricing.
- **Search & Analytics**: Product search, instant autocomplete suggestions, vendor sales dashboards, admin platform GMV metrics.
- **Notifications**: Strategy pattern multi-channel dispatch engine (In-App, Email, SMS, Push).
- **OpenAPI 3.1 Documentation**: Live interactive Swagger UI at `/docs/` and Redoc UI at `/`.

---

## 🐳 Quickstart with Docker

### 1. Clone & Environment Setup
Copy the environment variables template:

```bash
cp .env.example .env
```

### 2. Build & Run Containers
Spin up the PostgreSQL database and Django web server:

```bash
docker compose up -d --build
```

The containerized stack includes:
- **`web`**: Django API running on `http://localhost:8000` (Uvicorn ASGI)
- **`db`**: PostgreSQL 16 database running on `localhost:5432`

### 3. Check Container Status & Logs

```bash
docker compose ps
docker compose logs -f web
```

### 4. Create Superuser (Admin)

```bash
docker compose exec web python manage.py createsuperuser
```

---

## 💻 Local Development Setup (Without Docker)

```bash
# 1. Create & activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Linux/macOS

# 2. Install dependencies
pip install -r requirements/dev.txt

# 3. Apply database migrations
python manage.py migrate

# 4. Run development server
python manage.py runserver
```

---

## ⚡ Makefile Shortcuts

You can use `make` for quick commands:

| Command | Action |
|---------|--------|
| `make help` | Display list of all available commands |
| `make test` | Run full unit test suite locally |
| `make schema` | Validate & update OpenAPI `schema.yml` |
| `make docker-up` | Build & launch Docker stack (`web` + `db`) |
| `make docker-logs` | Tail live logs for `web` container |
| `make docker-migrate` | Apply migrations inside Docker |
| `make docker-test` | Run unit tests inside Docker |
| `make docker-superuser` | Create admin superuser inside Docker |
| `make docker-down` | Stop Docker containers |

---

## 🔄 CI/CD Pipeline

The project includes an automated GitHub Actions CI/CD workflow ([`.github/workflows/ci.yml`](file:///.github/workflows/ci.yml)) that triggers on push and pull request events:

1. **Automated System Checks**: Validates Django configuration and settings.
2. **PostgreSQL Test Suite**: Runs all 25 unit tests against a real PostgreSQL 16 service container.
3. **OpenAPI Schema Validation**: Verifies `schema.yml` integrity via `drf-spectacular`.
4. **Docker Container Build**: Compiles and verifies the `Dockerfile` with layer caching.



