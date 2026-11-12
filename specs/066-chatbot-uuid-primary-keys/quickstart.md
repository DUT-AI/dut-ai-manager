# Quickstart: Chatbot UUID Primary Keys Migration

## 1. Chạy Migration Alembic
```bash
cd backend
poetry run alembic upgrade head
```

## 2. Chạy Kiểm thử Backend
```bash
cd backend
poetry run pytest tests/unit/test_chatbot.py
```

## 3. Kiểm tra Frontend
```bash
cd frontend
npm run build
```
