# Hướng dẫn Chạy Nhanh và Xác minh Tính năng (Quickstart Guide)

**Feature Branch**: `specs/054-openapi-type-generation`  
**Date**: 2026-11-08  
**Spec**: [spec.md](./spec.md)

---

## 1. Điều kiện Tiên quyết (Prerequisites)

1. Máy tính đã cài đặt Node.js (`>= 20`), `npm`, Python (`>= 3.12`), và `uv`.
2. File môi trường `.env` đã được cấu hình hợp lệ (hoặc copy từ `.env.template`).

---

## 2. Các Bước Thực thi và Kiểm thử Đầu-Cuối (End-to-End Verification)

### Bước 1: Khởi động Backend Server
Trong terminal 1, khởi động FastAPI server ở cổng 8001:
```bash
make backend-dev
```
Xác nhận backend đã chạy bằng cách kiểm tra:
```bash
curl -s http://127.0.0.1:8001/api/v1/openapi.json | head -c 100
```
Kết quả mong đợi: Trả về chuỗi JSON bắt đầu bằng `{"openapi":"3.1.0",...}`.

---

### Bước 2: Cài đặt Thư viện và Chạy Sinh Type ở Frontend
Trong terminal 2:
```bash
# Cài đặt openapi-typescript (nếu chưa cài)
cd frontend && npm install -D openapi-typescript

# Thực thi lệnh sinh type
npm run generate:api
```
Hoặc dùng lệnh Makefile từ thư mục gốc:
```bash
make frontend-generate-api
```

**Kết quả mong đợi**:
- Tệp `frontend/src/types/api.generated.d.ts` được tạo hoặc cập nhật mới.
- Tìm thấy schema `HomeworkResponseDetail`, `HomeworkCreate`, v.v. Trong `components["schemas"]`.

---

### Bước 3: Xác minh Trải nghiệm Lập trình viên (Developer Experience & IntelliSense)
1. Mở một tệp TypeScript trong `frontend/src/features/homework/`.
2. Khai báo:
   ```typescript
   import type { Schema } from '@/types';
   type MyHomework = Schema<"HomeworkResponse">;
   ```
3. Thử gõ `Schema<"` trong IDE: Trình biên tập sẽ tự động gợi ý danh sách toàn bộ các schema của backend.
4. Thử truy cập thuộc tính sai trên `MyHomework`: IDE và `tsc` báo lỗi ngay lập tức.

---

### Bước 4: Kiểm tra Biên dịch và Zero-Regression
Chạy kiểm tra chất lượng toàn bộ dự án frontend:
```bash
cd frontend && npm run build && npm run lint
```
**Kết quả mong đợi**:
- Quá trình build Vite hoàn tất thành công (`vite build` exit code 0).
- Không có bất kỳ lỗi biên dịch TypeScript (`tsc`) nào.
