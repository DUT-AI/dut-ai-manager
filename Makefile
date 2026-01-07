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
docker-up: ## Start all docker containers
	docker-compose up -d

docker-down: ## Stop all docker containers
	docker-compose down

docker-restart: ## Restart all docker containers
	docker-compose restart

docker-logs: ## View docker logs
	docker-compose logs -f

docker-ps: ## List running containers
	docker-compose ps

docker-clean: ## Remove all containers and volumes
	docker-compose down -v --remove-orphans

# ==================== Database ====================
db-up: ## Start PostgreSQL only
	docker-compose up -d postgres

db-down: ## Stop PostgreSQL
	docker-compose stop postgres

db-logs: ## View PostgreSQL logs
	docker-compose logs -f postgres

db-shell: ## Access PostgreSQL shell
	docker-compose exec postgres psql -U postgres -d dut_ai_manager

# ==================== Backend ====================
backend-install: ## Install backend dependencies
	cd backend && uv sync

backend-dev: ## Run backend development server
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

backend-test: ## Run backend tests
	cd backend && uv run pytest

backend-lint: ## Lint backend code
	cd backend && uv run ruff check .

backend-format: ## Format backend code
	cd backend && uv run ruff format .

# ==================== Frontend ====================
frontend-install: ## Install frontend dependencies
	cd frontend && yarn install

frontend-dev: ## Run frontend development server
	cd frontend && yarn dev

frontend-build: ## Build frontend for production
	cd frontend && yarn build

frontend-preview: ## Preview production build
	cd frontend && yarn preview

frontend-lint: ## Lint frontend code
	cd frontend && yarn lint

# ==================== All ====================
install: backend-install frontend-install ## Install all dependencies

dev: ## Run all development servers (requires tmux or run in separate terminals)
	@echo "Run these commands in separate terminals:"
	@echo "  make docker-up"
	@echo "  make backend-dev"
	@echo "  make frontend-dev"

clean: docker-clean ## Clean all docker resources
	@echo "Cleaned!"
