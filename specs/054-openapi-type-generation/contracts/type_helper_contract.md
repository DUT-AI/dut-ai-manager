# Hợp đồng API Module: Type Helper Contract

**Feature Branch**: `specs/054-openapi-type-generation`  
**Date**: 2026-11-08  
**Spec**: [spec.md](../spec.md)

---

## 1. Mục đích
Quy định danh mục các generic type utilities được export từ `frontend/src/types/api.ts` nhằm hỗ trợ lập trình viên khai báo type ngắn gọn, an toàn và đồng bộ với cấu trúc `ApiResponse[T]` của dự án.

---

## 2. Danh mục Type Helper Xuất khẩu (`frontend/src/types/api.ts`)

### 2.1. `Schema<T>`
Trích xuất trực tiếp một Component Schema từ `components["schemas"]`.
```typescript
import type { components } from "./api.generated";

/**
 * Trích xuất một component schema từ FastAPI OpenAPI specification
 * @example
 * type Homework = Schema<"HomeworkResponse">;
 * type CreatePayload = Schema<"HomeworkCreate">;
 */
export type Schema<T extends keyof components["schemas"]> = components["schemas"][T];
```

### 2.2. `ApiPaths`
Alias cho toàn bộ `paths` của OpenAPI.
```typescript
import type { paths } from "./api.generated";

/**
 * Danh mục toàn bộ các Endpoint Paths được định nghĩa trong OpenAPI
 */
export type ApiPaths = paths;
```

### 2.3. `ApiResponseBody<T>`
Bọc trực tiếp một schema trong cấu trúc phong bì `ApiResponse<T>` chuẩn của dự án:
```typescript
import type { ApiResponse } from "./api.types";

/**
 * Trả về kiểu envelope ApiResponse chứa data là schema T
 * @example
 * type HomeworkDetailApiResponse = ApiResponseBody<"HomeworkResponseDetail">;
 */
export type ApiResponseBody<T extends keyof components["schemas"]> = ApiResponse<Schema<T>>;
```

### 2.4. `ApiData<Path, Method>`
Trích xuất trường `data` từ response code 200/201 của một endpoint cụ thể:
```typescript
/**
 * Trích xuất kiểu trả về của endpoint cụ thể (nếu endpoint có responses[200]["content"]["application/json"])
 */
export type ApiEndpointResponse<
  P extends keyof paths,
  M extends keyof paths[P] = "get" extends keyof paths[P] ? "get" : keyof paths[P]
> = paths[P][M] extends { responses: { 200: { content: { "application/json": infer R } } } }
  ? R
  : paths[P][M] extends { responses: { 201: { content: { "application/json": infer R } } } }
  ? R
  : unknown;
```

---

## 3. Quy chuẩn Sử dụng trong Service và Hook

Trong các service gọi API (`*.service.ts`):
```typescript
import axiosInstance from '@/services/axiosInstance';
import type { ApiResponse, Schema } from '@/types';

export const homeworkService = {
  baseUrl: 'homeworks',

  async getById(id: number): Promise<Schema<"HomeworkResponseDetail">> {
    const response = await axiosInstance.get<ApiResponse<Schema<"HomeworkResponseDetail">>>(
      `/${this.baseUrl}/${id}`
    );
    return response.data.data!;
  },
};
```
