# Quickstart: Meeting Check-In Domain Refactor

## How to Test

### 1. Run Unit Tests
```bash
uv run --directory backend pytest tests/unit/test_meeting_domain.py -v
uv run --directory backend pytest tests/unit/test_meeting_use_cases.py -v
```

### 2. Run Ruff Linting
```bash
uv run --directory backend ruff check app/meeting/
```

### 3. Check All Tests
```bash
uv run --directory backend pytest tests/unit/
```
