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

# ==================== Database Tunnel ====================
db-tunnel-start: ## Start Cloudflare Tunnel to remote dev database (run in background)
	@echo "🔗 Starting Cloudflare Tunnel to remote dev database..."
	@. .env 2>/dev/null; cloudflared access tcp --hostname $${CLOUDFLARE_DB_TUNNEL_HOST} --url localhost:5432 &
	@sleep 3
	@echo "✅ Tunnel started on localhost:5432"

db-tunnel-stop: ## Stop Cloudflare Tunnel
	@pkill -f "cloudflared access tcp" 2>/dev/null || true
	@echo "✅ Tunnel stopped"

# Helper: Run command with tunnel (internal use)
define with_tunnel
	@. .env 2>/dev/null; \
	cloudflared access tcp --hostname $${CLOUDFLARE_DB_TUNNEL_HOST} --url localhost:5432 & \
	TUNNEL_PID=$$!; \
	sleep 3; \
	cd backend && POSTGRES_SERVER=localhost $(1); \
	EXIT_CODE=$$?; \
	kill $$TUNNEL_PID 2>/dev/null || true; \
	exit $$EXIT_CODE
endef

# ==================== Migrations (auto-starts tunnel) ====================
migrate-create: ## Create a new migration (usage: make migrate-create msg="description")
	$(call with_tunnel,uv run alembic revision --autogenerate -m "$(msg)")

migrate-up: ## Apply all migrations
	$(call with_tunnel,uv run alembic upgrade head)

migrate-up-prod: ## Apply all migrations
	cd backend && uv run alembic upgrade head	

migrate-down: ## Rollback last migration
	$(call with_tunnel,uv run alembic downgrade -1)

migrate-history: ## Show migration history
	$(call with_tunnel,uv run alembic history)

migrate-current: ## Show current migration
	$(call with_tunnel,uv run alembic current)

seed-db: ## Seed permissions from enums into database
	$(call with_tunnel,uv run python -m app.scripts.seed_permissions)

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
