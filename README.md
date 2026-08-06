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
