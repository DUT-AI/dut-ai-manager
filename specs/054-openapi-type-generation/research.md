# Nghiên cứu Kỹ thuật: Đồng bộ hóa hợp đồng API và sinh Type tự động cho Frontend từ OpenAPI Backend

**Feature Branch**: `specs/054-openapi-type-generation`  
**Date**: 2026-11-08  
**Spec**: [spec.md](./spec.md)

---

## 1. Lựa chọn Công cụ sinh mã Type (Toolchain Selection)

### Quyết định (Decision)
Sử dụng thư viện **`openapi-typescript`** (phiên bản `^7.x`) cài đặt trong `devDependencies` của `frontend/package.json`.

### Lý do lựa chọn (Rationale)
1. **Zero Runtime Overhead**: `openapi-typescript` chỉ sinh ra các định nghĩa kiểu TypeScript thuần túy (`.d.ts` hoặc `.ts`), hoàn toàn không làm phình to kích thước bundle production của ứng dụng frontend (0 KB bundle size).
2. **Hỗ trợ đầy đủ OpenAPI 3.1 & Pydantic v2**: FastAPI phiên bản mới xuất chuẩn OpenAPI 3.1. `openapi-typescript` v7 là thư viện tiên phong hỗ trợ phân giải đầy đủ JSON Schema draft 2020-12, bao gồm các cấu trúc `anyOf`, `allOf`, `const`, `nullable` mà Pydantic v2 tạo ra.
3. **Phù hợp với kiến trúc hiện hữu**: Hệ thống đã có sẵn `axiosInstance` được cấu hình chặt chẽ theo Hiến chương (Điều XV - Unified Client Networking). Dự án không cần các công cụ sinh mã client tự động cồng kềnh (như `orval` hay `swagger-codegen` tự sinh axios client riêng biệt), mà chỉ cần hệ thống Type Definition để gán kiểu trực tiếp vào `axiosInstance.get<...>()` và `useQuery<...>()`.
4. **Đúng theo đặc tả của người dùng**: Người dùng yêu cầu cấu trúc trích xuất schema qua `components["schemas"]` và `paths`.

### Các giải pháp thay thế đã đánh nhắc (Alternatives Considered)
- **`orval`**: Quá nặng, tự động sinh code React Query hooks và fetch client, gây xung đột với chuẩn tổ chức hook và `axiosInstance` hiện tại của dự án.
- **`swagger-typescript-api`**: Tạo ra các class/interface phức tạp, hỗ trợ OpenAPI 3.1 kém hơn so với `openapi-typescript` v7.
- **Viết tay thủ công (Hiện trạng)**: Rất dễ bị lệch kiểu (type drifting) mỗi khi backend sửa đổi trường dữ liệu; vi phạm nguyên tắc Single Source of Truth (Điều X của Hiến chương).

---

## 2. Cơ chế thực thi và xử lý ngoại lệ Live HTTP URL

### Quyết định (Decision)
Cấu hình script `generate:api` trong `frontend/package.json` trỏ trực tiếp tới `http://127.0.0.1:8001/api/v1/openapi.json`, kết hợp mục tiêu `frontend-generate-api` trong root `Makefile`. Khi server backend không phản hồi (offline), hiển thị thông báo lỗi rõ ràng hướng dẫn khởi động backend server.

### Chi tiết cấu hình:
1. **NPM Script (`frontend/package.json`)**:
   ```json
   "generate:api": "openapi-typescript http://127.0.0.1:8001/api/v1/openapi.json -o src/types/api.generated.d.ts"
   ```
2. **Makefile Target (`Makefile`)**:
   ```makefile
   frontend-generate-api: ## Sinh TypeScript types từ FastAPI OpenAPI đang chạy
   	cd frontend && npm run generate:api
   ```
3. **Xử lý khi backend offline**: Khi cổng `8001` chưa mở, `openapi-typescript` trả về mã lỗi kết nối `ECONNREFUSED`. Makefile có thể bọc kiểm tra curl hoặc ghi chú rõ trong tài liệu để lập trình viên chạy `make backend-dev` trước.

---

## 3. Thiết kế Type Helpers cho Envelope `ApiResponse[T]`

### Quyết định (Decision)
Xây dựng module tập trung `frontend/src/types/api.ts` cung cấp các type helpers chuẩn hóa:
1. `Schema<T extends keyof components["schemas"]>`: Trích xuất trực tiếp component schema từ FastAPI OpenAPI.
2. `ApiPaths`: Alias cho `paths` của toàn bộ hệ thống API.
3. `ApiResponse<T>`: Tái sử dụng envelope chuẩn từ `api.types.ts`.
4. `ApiData<P extends keyof paths, M extends keyof paths[P]>`: Trích xuất payload thực tế của thuộc tính `data` từ response 200/201 của một route cụ thể.

### Mẫu thiết kế kỹ thuật (Design Pattern):
```typescript
import type { components, paths } from "./api.generated";
import type { ApiResponse } from "./api.types";

/**
 * Trích xuất một component schema từ đặc tả OpenAPI của FastAPI
 * Ví dụ: Schema<"HomeworkResponse">
 */
export type Schema<T extends keyof components["schemas"]> = components["schemas"][T];

/**
 * Toàn bộ danh mục đường dẫn API định nghĩa từ OpenAPI
 */
export type ApiPaths = paths;

/**
 * Trích xuất dữ liệu bên trong envelope ApiResponse của một schema cụ thể
 */
export type ApiResponseBody<T extends keyof components["schemas"]> = ApiResponse<Schema<T>>;
```

---

## 4. Phạm vi Áp dụng Thử nghiệm (Pilot Scope - Module Homework)

### Quyết định (Decision)
Chọn module **Homework** (`frontend/src/features/homework/`) làm phạm vi thử nghiệm mẫu:
- **Lý do**:
  1. Module Homework có đầy đủ các tương tác: Danh sách phân trang (`HomeworkResponse[]`), Chi tiết bài tập (`HomeworkResponseDetail`), Tạo mới/Cập nhật (`HomeworkCreate`, `HomeworkUpdate`), Báo cáo nộp bài (`HomeworkReportResponse`), Trạng thái nộp bài (`HomeworkSubmissionStatusResponse`).
  2. Vừa được chuẩn hóa nghiêm ngặt trong Spec 053 (`coding_exercises`, `is_passed`), giúp kiểm chứng tính đồng bộ ngay lập tức.
  3. Quá trình di chuyển sẽ thay thế các interface viết tay trong `frontend/src/features/homework/types/homework.types.ts` bằng các type ánh xạ từ `Schema<"...">`, đồng thời giữ nguyên các Zod schemas phục vụ form validation (hoặc suy diễn từ kiểu dữ liệu nếu cần) để đảm bảo không làm gián đoạn UI components.
