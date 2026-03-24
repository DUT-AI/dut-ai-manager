.PHONY: help install dev build start stop restart logs clean

# Colors
GREEN := \033[0;32m
NC := \033[0m

help: ## Show this help
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

# ==================== Docker ====================
docker-up: ## Start all docker containers (local dev mode)
	docker compose up -d

docker-down: ## Stop all docker containers
	docker compose down

docker-restart: ## Restart all docker containers
	docker compose restart

docker-logs: ## View docker logs
	docker compose logs -f

docker-ps: ## List running containers
	docker compose ps

docker-clean: ## Remove all containers and volumes
	docker compose down -v --remove-orphans

docker-build: ## Build all docker images
	docker compose build



# ==================== Migrations (auto-starts tunnel) ====================
migrate-create: ## Create a new migration (usage: make migrate-create msg="description")
	cd backend && uv run alembic revision --autogenerate -m "$(msg)"

migrate-up: ## Apply all migrations
	cd backend && uv run alembic upgrade head

migrate-down: ## Rollback last migration
	cd backend && uv run alembic downgrade -1

migrate-history: ## Show migration history
	cd backend && uv run alembic history

migrate-current: ## Show current migration
	cd backend && uv run alembic current

seed-db: ## Seed permissions from enums into database
	cd backend && uv run python -m app.scripts.seed_permissions

# ==================== Backend ====================
backend-install: ## Install backend dependencies
	cd backend && uv sync

backend-dev: ## Run backend with remote dev database via Cloudflare Tunnel
	@cd backend && POSTGRES_SERVER=localhost uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001; \


backend-test: ## Run backend tests
	cd backend && uv run pytest

backend-lint: ## Lint backend code
	cd backend && uv run ruff check .

backend-format: ## Format backend code
	cd backend && uv run ruff format .

# ==================== Frontend ====================
frontend-install: ## Install frontend dependencies
	cd frontend && npm install

frontend-dev: ## Run frontend development server
	cd frontend && npm run dev

frontend-build: ## Build frontend for production
	cd frontend && npm run build

frontend-preview: ## Preview production build
	cd frontend && npm run preview

frontend-lint: ## Lint frontend code
	cd frontend && npm run lint

# ==================== All ====================
install: backend-install frontend-install ## Install all dependencies

dev: ## Run all development servers (requires tmux or run in separate terminals)
	@echo "Run these commands in separate terminals:"
	@echo "  make backend-dev"
	@echo "  make frontend-dev"

clean: docker-clean ## Clean all docker resources
	@echo "Cleaned!"

# ==================== Backend V2 (Clean Architecture) ====================
backend-v2-install: ## Install backend-v2 dependencies
	cd backend_v2 && uv sync

backend-v2-dev: ## Run backend-v2 discovery
	cd backend_v2 && uv run uvicorn app.main:app --reload --port 8032

backend-v2-quality: ## Run quality checks for backend-v2
	make -C backend_v2 quality

backend-v2-test: ## Run backend-v2 tests
	make -C backend_v2 test
