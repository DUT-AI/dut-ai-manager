# Quickstart & Verification Guide: Homework Submission Metadata

**Feature**: `056-standardize-submission-metadata`  
**Date**: 2026-11-08

---

## 1. Kiểm tra Backend & Schema
1. Chạy unit tests cho homework:
   ```bash
   poetry run pytest backend/tests/test_homework/ -v
   ```
2. Kiểm tra type check Backend:
   ```bash
   poetry run mypy backend/app/homework
   ```

---

## 2. Đồng bộ OpenAPI & Kiểm tra Frontend
1. Xuất OpenAPI schema từ Backend:
   ```bash
   poetry run python -c "
   import json
   from app.main import app
   print(json.dumps(app.openapi()))
   " > frontend/openapi.json
   ```
2. Sinh types TypeScript tự động:
   ```bash
   cd frontend && npm run generate:api
   ```
3. Kiểm tra tính toàn vẹn kiểu tĩnh:
   ```bash
   cd frontend && npx tsc -b
   ```
4. Kiểm tra build production:
   ```bash
   cd frontend && npm run build
   ```
