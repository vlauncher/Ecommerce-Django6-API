.PHONY: help install run migrations migrate flush seed superuser test schema \
        docker-up docker-down docker-build docker-logs docker-ps \
        docker-migrate docker-migrations docker-test docker-superuser docker-schema docker-clean

PYTHON = .venv/bin/python
MANAGE = $(PYTHON) manage.py

# Default target
help:
	@echo "=========================================================================="
	@echo " 🏪 Django 6 E-Commerce Marketplace API Commands"
	@echo "=========================================================================="
	@echo " Local Commands:"
	@echo "   make install            Install local Python dependencies"
	@echo "   make run                Start Celery Worker & Django local dev server"
	@echo "   make migrations         Generate new Django database migrations"
	@echo "   make migrate            Apply database migrations locally"
	@echo "   make flush              Wipe & flush all database tables"
	@echo "   make seed               Seed 10 products, categories & vendor data"
	@echo "   make superuser          Create a new Django superuser (admin)"
	@echo "   make test               Run test suite across all 12 domain apps"
	@echo "   make schema             Generate & validate OpenAPI 3.1 schema.yml"
	@echo ""
	@echo " Docker Commands:"
	@echo "   make docker-up          Build and start Docker containers in background"
	@echo "   make docker-down        Stop Docker containers"
	@echo "   make docker-build       Rebuild Docker images without cache"
	@echo "   make docker-logs        Tail live logs for the web container"
	@echo "   make docker-ps          List running Docker containers"
	@echo "   make docker-migrations  Run makemigrations inside web container"
	@echo "   make docker-migrate     Run migrate inside web container"
	@echo "   make docker-test        Run full test suite inside web container"
	@echo "   make docker-superuser   Create superuser inside web container"
	@echo "   make docker-schema      Generate & validate schema inside web container"
	@echo "   make docker-clean       Stop containers and delete volumes (data wipe)"
	@echo "=========================================================================="

# ------------------------------------------------------------------------------
# LOCAL VIRTUALENV COMMANDS
# ------------------------------------------------------------------------------

install:
	pip install -r requirements/dev.txt

run:
	@echo "Starting Celery Worker & Django ASGI Server..."
	$(PYTHON) -m celery -A core worker -l info --pool=solo &
	$(MANAGE) runserver

migrations:
	$(MANAGE) makemigrations

migrate:
	$(MANAGE) migrate

flush:
	$(MANAGE) flush --no-input

seed:
	$(PYTHON) seed_catalog.py

superuser:
	$(MANAGE) createsuperuser

test:
	$(MANAGE) test vendors catalog reviews accounts cart orders payments inventory promotions search notifications


schema:
	$(MANAGE) spectacular --validate --file schema.yml

# ------------------------------------------------------------------------------
# DOCKER COMMANDS
# ------------------------------------------------------------------------------

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

docker-build:
	docker compose build --no-cache

docker-logs:
	docker compose logs -f web

docker-ps:
	docker compose ps

docker-migrations:
	docker compose exec web python manage.py makemigrations

docker-migrate:
	docker compose exec web python manage.py migrate

docker-test:
	docker compose exec web python manage.py test vendors catalog reviews accounts cart orders payments inventory promotions search notifications

docker-superuser:
	docker compose exec web python manage.py createsuperuser

docker-schema:
	docker compose exec web python manage.py spectacular --validate --file schema.yml

docker-clean:
	docker compose down -v
