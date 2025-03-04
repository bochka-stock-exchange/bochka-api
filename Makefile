# Makefile for FastAPI project

# Variables
DOCKER_COMPOSE = docker-compose
DOCKER_COMPOSE_PROD = docker-compose -f docker-compose.prod.yml
UV = uv
PRE_COMMIT = pre-commit
PYTEST = pytest
RUFF = ruff
UVICORN = uvicorn

# Help command
help:
	@echo "Available commands:"
	@echo "  help               - Show this help message"
	@echo "  up                 - Start the development environment using docker-compose"
	@echo "  down               - Stop the development environment"
	@echo "  up-prod            - Start the production environment using docker-compose.prod.yml"
	@echo "  down-prod          - Stop the production environment"
	@echo "  migrate            - Run database migrations"
	@echo "  install-deps       - Install dependencies using uv"
	@echo "  check              - Run pre-commit checks"
	@echo "  check-install      - Install pre-commit hooks"
	@echo "  lint               - Perform linting on all files using ruff"
	@echo "  format             - Format all files using ruff format"
	@echo "  test               - Test the app (runs lint and format first)"
	@echo "  start              - Start the app using uvicorn"

# Start the development environment
up:
	$(DOCKER_COMPOSE) up -d

# Stop the development environment
down:
	$(DOCKER_COMPOSE) down

# Start the production environment
up-prod:
	$(DOCKER_COMPOSE_PROD) up -d

# Stop the production environment
down-prod:
	$(DOCKER_COMPOSE_PROD) down

# Run database migrations
migrate:
	$(DOCKER_COMPOSE) exec web alembic upgrade head

# Install dependencies using uv
install-deps:
	$(UV) sync --all-extras --dev

# Run pre-commit checks
check:
	$(UV) run $(PRE_COMMIT) run --all-files

# Install pre-commit hooks
pre-commit-install:
	$(PRE_COMMIT) install

# Perform linting on all files using ruff
lint:
	$(UV) run $(RUFF) check --fix .

# Format all files using ruff format
format:
	$(UV) run $(RUFF) format .

# Test the app (runs lint and format first)
test: lint format
	$(UV) run $(PYTEST) -v --durations=0 --cov .

# Start the app using uvicorn
start:
	$(UV) run $(UVICORN) src.app.main:app --host 0.0.0.0 --port 8000 --reload

.PHONY: help up down up-prod down-prod migrate install-deps pre-commit pre-commit-install lint format test start
