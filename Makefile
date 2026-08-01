UV ?= uv
COMPOSE ?= docker compose
ENV_FILE ?= .env
IMAGE_NAME ?= relay-agent-platform
IMAGE_TAG ?= dev
PYTEST_ARGS ?=
MIGRATION_MESSAGE ?=

.DEFAULT_GOAL := help

.PHONY: help init sync sync-frozen lock lock-check hooks format format-check lint \
	typecheck unit integration test coverage check check-migrations api worker \
	migrate-up migrate-down migration compose-up compose-down compose-logs \
	postgres-up build

help: ## Show the available Phase 1 commands.
	@echo "Release 0 - Phase 1"
	@echo ""
	@echo "Setup"
	@echo "  make init              Create .env, sync dependencies, install hooks"
	@echo "  make sync              Resolve and sync all dependency groups"
	@echo "  make sync-frozen       Sync exactly from uv.lock (CI/reproducible builds)"
	@echo ""
	@echo "Quality"
	@echo "  make format            Format Python sources"
	@echo "  make check             Run Phase 1 static checks and unit tests"
	@echo "  make integration       Run tests marked as integration"
	@echo "  make coverage          Run tests with branch coverage"
	@echo ""
	@echo "Runtime"
	@echo "  make api               Start the FastAPI development server"
	@echo "  make worker            Start the worker process"
	@echo "  make compose-up        Start the local Compose stack"
	@echo "  make migrate-up        Apply all database migrations"
	@echo ""
	@echo "Build"
	@echo "  make build             Build the shared application image"

$(ENV_FILE): .env.example
	@cp .env.example $(ENV_FILE)
	@echo "Created $(ENV_FILE) from .env.example"

init: $(ENV_FILE) sync hooks ## Prepare a local development environment.

sync: ## Resolve and install runtime and development dependencies.
	$(UV) sync --all-groups

sync-frozen: ## Install exactly what is recorded in uv.lock.
	$(UV) sync --frozen --all-groups

lock: ## Update uv.lock after an intentional dependency change.
	$(UV) lock

lock-check: ## Verify that uv.lock matches pyproject.toml.
	$(UV) lock --check

hooks: ## Install the repository's pre-commit hooks.
	$(UV) run pre-commit install

format: ## Format source and test files.
	$(UV) run ruff format src tests migrations scripts
	$(UV) run ruff check --fix src tests migrations scripts

format-check: ## Verify formatting without changing files.
	$(UV) run ruff format --check src tests migrations scripts

lint: ## Run Ruff lint checks.
	$(UV) run ruff check src tests migrations scripts

typecheck: ## Run strict static type checking.
	$(UV) run mypy

unit: ## Run tests that do not require external infrastructure.
	$(UV) run pytest -m "not integration" $(PYTEST_ARGS)

integration: ## Run PostgreSQL-backed integration tests.
	$(UV) run pytest -m integration $(PYTEST_ARGS)

test: ## Run the complete Phase 1 test suite.
	$(UV) run pytest $(PYTEST_ARGS)

coverage: ## Run tests and report branch coverage.
	$(UV) run pytest --cov=agent_platform --cov-report=term-missing $(PYTEST_ARGS)

check-migrations: ## Run migration consistency validation used by CI.
	$(UV) run python scripts/check_migrations.py

check: format-check lint typecheck unit check-migrations lock-check ## Run the Phase 1 CI checks.

api: ## Start the API runtime with reload enabled for local development.
	$(UV) run uvicorn agent_platform.api.app:app --host 0.0.0.0 --port 8000 --reload

worker: ## Start the independent worker runtime.
	$(UV) run python -m agent_platform.workers.main

migrate-up: ## Apply all pending migrations.
	$(UV) run alembic upgrade head

migrate-down: ## Roll back one migration revision.
	$(UV) run alembic downgrade -1

migration: ## Create a migration: make migration MIGRATION_MESSAGE="description"
	@test -n "$(MIGRATION_MESSAGE)" || (echo "MIGRATION_MESSAGE is required" && exit 2)
	$(UV) run alembic revision --autogenerate -m "$(MIGRATION_MESSAGE)"

compose-up: $(ENV_FILE) ## Start all local services in the background.
	$(COMPOSE) --env-file $(ENV_FILE) up --build -d

postgres-up: $(ENV_FILE) ## Start only the local PostgreSQL service.
	$(COMPOSE) --env-file $(ENV_FILE) up -d postgres

compose-down: ## Stop the local Compose stack without deleting volumes.
	$(COMPOSE) --env-file $(ENV_FILE) down

compose-logs: ## Follow logs from the local Compose stack.
	$(COMPOSE) --env-file $(ENV_FILE) logs --follow

build: ## Build the shared API/worker/migration application image.
	docker build \
		--build-arg BUILD_VERSION=0.1.0-dev \
		--build-arg COMMIT_SHA=$$(git rev-parse HEAD) \
		--tag $(IMAGE_NAME):$(IMAGE_TAG) \
		.
