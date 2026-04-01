.PHONY: quality format sort-imports typecheck lint bandit safety test

# Chạy toàn bộ kiểm tra chất lượng (tương đương các lệnh bạn liệt kê)
quality: format sort-imports typecheck lint bandit safety test

format:
	uv run black app tests

sort-imports:
	uv run isort app tests

typecheck:
	uv run mypy app

lint:
	uv run flake8 app

bandit:
	uv run bandit -r app

# Dùng `check` (open DB) để chạy không cần đăng nhập; `safety scan` (v3) có thể hỏi R/L.
safety:
	uv run safety check

test:
	PYTHONPATH=. uv run pytest tests
