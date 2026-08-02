.PHONY: help venv install migrate makemigrations run test check createsuperuser docker-up docker-down docker-build docker-prod-up docker-prod-down clean

# Python executable
PYTHON = venv/bin/python
PIP = venv/bin/pip
MANAGE = $(PYTHON) manage.py

help:
	@echo "Available commands:"
	@echo "  make venv           - Create virtual environment"
	@echo "  make install        - Install development dependencies"
	@echo "  make migrate        - Apply database migrations"
	@echo "  make makemigrations - Generate new database migrations"
	@echo "  make run            - Run Django development server"
	@echo "  make test           - Run Django test suite"
	@echo "  make check          - Run Django system deployment check"
	@echo "  make createsuperuser- Create a new superuser"
	@echo "  make docker-up      - Run dev environment with Docker Compose"
	@echo "  make docker-down    - Stop dev Docker Compose services"
	@echo "  make docker-build   - Rebuild dev Docker Compose containers"
	@echo "  make docker-prod-up - Run production environment with Docker Compose"
	@echo "  make docker-prod-down- Stop production Docker Compose services"
	@echo "  make clean          - Clean python cache files and sqlite database"

venv:
	python3 -m venv venv

install: venv
	$(PIP) install -r requirements/dev.txt

migrate:
	$(MANAGE) migrate

makemigrations:
	$(MANAGE) makemigrations

run:
	$(PYTHON) -m uvicorn core.asgi:application --reload --port 8000

test:
	$(MANAGE) test apps.users.tests

check:
	$(MANAGE) check

createsuperuser:
	$(MANAGE) createsuperuser

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-build:
	docker-compose up -d --build

docker-prod-up:
	docker-compose -f docker-compose.prod.yml up -d --build

docker-prod-down:
	docker-compose -f docker-compose.prod.yml down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -f db.sqlite3
