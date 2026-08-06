# Ecommerce Django 6.0 API

A production-grade, scalable, and reliable Django 6.0 REST API project setup.

## Features
- **Django 6.0**: Built-in background tasks framework (`django.tasks`), native CSP support.
- **Architecture**: Modular layout with domain-based `apps/` directory and split settings (`base.py`, `dev.py`, `prod.py`).
- **REST API**: Django REST Framework + SimpleJWT authentication, versioning (`/api/v1/`), pagination, throttling.
- **Database**: SQLite for development, PostgreSQL 16 for production with health checks & persistent connections.
- **Caching**: Redis integration with `django-redis`.
- **Docker**: Multi-stage Dockerfile and Docker Compose setups for development and production.
- **Multishop tenancy**: Shared users, shop memberships, role-based access, and email invitations.

## Multishop API

Authentication is account-wide. Shop-scoped requests select a shop by its slug and authorize the bearer token against that shop's membership.

- `POST /api/v1/shops/` creates a shop and assigns the authenticated user as owner.
- `GET/PATCH /api/v1/shops/{shop_slug}` reads or updates a shop.
- `GET /api/v1/shops/{shop_slug}/members` lists members for owners and managers.
- `POST /api/v1/shops/{shop_slug}/invitations` invites a member by email.
- `POST /api/v1/invitations/{token}/accept` accepts an invitation.
- `GET /api/v1/shops/{shop_slug}/users/profile` returns the authenticated user's profile with shop membership context.
- `POST /api/v1/shops/{shop_slug}/coupons` creates a shop coupon backed by a promotion rule.
- `POST /api/v1/cart/coupon` validates and applies a coupon to the authenticated customer's cart.
- `POST /api/v1/checkout` revalidates the coupon, records the discount snapshot, and consumes the redemption atomically.

## Management API

Operational resources use a consistent shop-scoped CRUD pattern:

```text
/api/v1/manage/shops/{shop_slug}/{resource}
/api/v1/manage/shops/{shop_slug}/{resource}/{id}
```

These routes support list, create, retrieve, update, and delete operations for catalog, inventory, promotions, coupons, shipping, tax, gift cards, seller orders, shipments, conversations, offers, reviews, disputes, and payout resources. Ledger, payment-event, redemption, and payment records are immutable and expose read/reconciliation workflows instead of destructive updates.

## Getting Started

### Local Development (Virtual Environment)
1. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
2. Install development dependencies:
   ```bash
   pip install -r requirements/dev.txt
   ```
3. Run migrations and start server:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

### Docker Development
1. Start containers:
   ```bash
   docker-compose up --build
   ```
