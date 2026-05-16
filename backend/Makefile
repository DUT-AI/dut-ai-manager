.PHONY: quality format sort-imports typecheck lint bandit safety test

# Chạy toàn bộ kiểm tra chất lượng
quality: format lint typecheck bandit safety test

format:
	uv run ruff format app tests

typecheck:
	uv run ty check app --exclude alembic/ --exclude tests/ --exclude scripts/ --exclude app/scripts/ --force-exclude

lint:
	uv run ruff check app tests --fix

bandit:
	uv run bandit -r app

# Dùng `check` (open DB) để chạy không cần đăng nhập; `safety scan` (v3) có thể hỏi R/L.
safety:
	uv run safety check

test:
	PYTHONPATH=. uv run pytest tests
