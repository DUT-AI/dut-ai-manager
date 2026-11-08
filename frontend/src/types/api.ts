import type { components, paths } from './api.generated';
import type { ApiResponse } from './api.types';

/**
 * Trích xuất một component schema từ FastAPI OpenAPI specification
 * @example
 * type Homework = Schema<"HomeworkResponse">;
 * type CreatePayload = Schema<"HomeworkCreate">;
 */
export type Schema<T extends keyof components['schemas']> = components['schemas'][T];

/**
 * Danh mục toàn bộ các Endpoint Paths được định nghĩa trong OpenAPI
 */
export type ApiPaths = paths;

/**
 * Trả về kiểu envelope ApiResponse chứa data là schema T
 * @example
 * type HomeworkDetailApiResponse = ApiResponseBody<"HomeworkResponseDetail">;
 */
export type ApiResponseBody<T extends keyof components['schemas']> = ApiResponse<Schema<T>>;

/**
 * Trích xuất kiểu trả về của endpoint cụ thể (nếu endpoint có responses[200/201]["content"]["application/json"])
 */
export type ApiEndpointResponse<
  P extends keyof paths,
  M extends keyof paths[P] = 'get' extends keyof paths[P] ? 'get' : keyof paths[P],
> = paths[P][M] extends { responses: { 200: { content: { 'application/json': infer R } } } }
  ? R
  : paths[P][M] extends { responses: { 201: { content: { 'application/json': infer R } } } }
    ? R
    : unknown;
