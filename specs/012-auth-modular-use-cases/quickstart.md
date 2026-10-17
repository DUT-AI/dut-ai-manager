# Quickstart & Verification: Kiểm Thử Auth Modular Use Cases

**Feature**: `012-auth-modular-use-cases` | **Date**: 2026-10-17

## 1. Kiểm Tra Tĩnh

Xác nhận không còn bất kỳ dòng nào tham chiếu tới `use_cases.py` cũ:
```bash
grep -rn "app.auth.application.use_cases" backend/
```
Kết quả mong đợi: Không có dòng nào.

## 2. Kiểm Thử Đơn Vị & API

Chạy bộ test API xác thực qua virtual environment:
```bash
backend/.venv/bin/pytest backend/tests/api/test_auth_api.py -v
```

Kiểm tra toàn bộ test suite để đảm bảo không có regression chéo:
```bash
backend/.venv/bin/pytest backend/tests/ -v
```
