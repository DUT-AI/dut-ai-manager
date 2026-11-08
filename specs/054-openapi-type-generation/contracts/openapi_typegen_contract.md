# Hợp đồng Tích hợp: OpenAPI Typegen CLI Contract

**Feature Branch**: `specs/054-openapi-type-generation`  
**Date**: 2026-11-08  
**Spec**: [spec.md](../spec.md)

---

## 1. Mục đích
Quy định thông số kỹ thuật, cấu hình câu lệnh, đường dẫn tệp và hành vi giao tiếp giữa quy trình sinh mã TypeScript ở Frontend và endpoint OpenAPI của FastAPI Backend.

---

## 2. Thông số Endpoint Backend

- **Giao thức**: HTTP / JSON
- **Địa chỉ Host**: `http://127.0.0.1:8001`
- **Đường dẫn Endpoint**: `/api/v1/openapi.json`
- **Phương thức**: `GET`
- **Chuẩn dữ liệu**: OpenAPI Specification v3.1.0
- **Tiêu chuẩn phản hồi**:
  - `Content-Type`: `application/json`
  - Trường bắt buộc cấp gốc: `openapi`, `info`, `paths`, `components.schemas`

---

## 3. Cấu hình Script Frontend

### 3.1. NPM Script (`frontend/package.json`)
```json
{
  "scripts": {
    "generate:api": "openapi-typescript http://127.0.0.1:8001/api/v1/openapi.json -o src/types/api.generated.d.ts"
  }
}
```

### 3.2. Makefile Automation (`Makefile`)
```makefile
frontend-generate-api: ## Sinh TypeScript types từ FastAPI OpenAPI đang chạy
	@echo "🔄 Đang sinh TypeScript types từ http://127.0.0.1:8001/api/v1/openapi.json..."
	cd frontend && npm run generate:api
```

---

## 4. Xử lý Trạng thái Ngoại lệ (Error States)

| Mã lỗi / Tình huống | Nguyên nhân | Hành vi mong đợi |
|---------------------|-------------|------------------|
| `ECONNREFUSED 127.0.0.1:8001` | Backend server chưa chạy | Lệnh dừng với exit code != 0, in thông báo rõ ràng: kiểm tra xem `make backend-dev` đã được khởi động chưa |
| HTTP 404 Not Found | Sai đường dẫn `openapi_url` | Kiểm tra lại cấu hình `openapi_url` trong `backend/app/main.py` (chuẩn là `/api/v1/openapi.json`) |
| Lỗi cú pháp JSON / Schema lỗi | FastAPI router khai báo kiểu Pydantic không hợp lệ | `openapi-typescript` hiển thị chi tiết schema parser error |
