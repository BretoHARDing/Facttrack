.PHONY: help up down build logs shell-api shell-db migrate migrate-down test lint format

DOCKER_COMPOSE = docker compose

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Start all services
	$(DOCKER_COMPOSE) up -d

up-build: ## Build images then start all services
	$(DOCKER_COMPOSE) up -d --build

down: ## Stop all services
	$(DOCKER_COMPOSE) down

down-volumes: ## Stop all services and remove volumes (destructive)
	$(DOCKER_COMPOSE) down -v

build: ## Build all Docker images
	$(DOCKER_COMPOSE) build

logs: ## Tail logs for all services
	$(DOCKER_COMPOSE) logs -f

logs-api: ## Tail API logs
	$(DOCKER_COMPOSE) logs -f api

logs-worker: ## Tail worker logs
	$(DOCKER_COMPOSE) logs -f worker

shell-api: ## Open a shell in the API container
	$(DOCKER_COMPOSE) exec api bash

shell-db: ## Open a psql shell in the postgres container
	$(DOCKER_COMPOSE) exec postgres psql -U $${POSTGRES_USER:-facttrack} $${POSTGRES_DB:-facttrack}

migrate: ## Run Alembic migrations (upgrade head)
	$(DOCKER_COMPOSE) exec api alembic upgrade head

migrate-down: ## Rollback last Alembic migration
	$(DOCKER_COMPOSE) exec api alembic downgrade -1

migrate-history: ## Show Alembic migration history
	$(DOCKER_COMPOSE) exec api alembic history

test: ## Run backend tests
	$(DOCKER_COMPOSE) exec api pytest tests/ -v

lint: ## Lint backend code with ruff
	$(DOCKER_COMPOSE) exec api ruff check app/

format: ## Format backend code with ruff
	$(DOCKER_COMPOSE) exec api ruff format app/

env: ## Copy .env.example to .env if .env does not exist
	@test -f .env || (cp .env.example .env && echo "Created .env from .env.example — update secrets before use.")

restart-api: ## Restart the API container
	$(DOCKER_COMPOSE) restart api

restart-worker: ## Restart the worker container
	$(DOCKER_COMPOSE) restart worker

ps: ## Show container status
	$(DOCKER_COMPOSE) ps
