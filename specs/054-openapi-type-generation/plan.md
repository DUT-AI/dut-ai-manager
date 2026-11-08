# Implementation Plan: Đồng bộ hóa hợp đồng API và sinh Type tự động cho Frontend từ OpenAPI Backend

**Branch**: `054-openapi-type-generation` | **Date**: 2026-11-08 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/054-openapi-type-generation/spec.md`

## Summary

Thiết lập cơ chế Single Source of Truth giữa Backend FastAPI và Frontend React bằng cách tích hợp công cụ `openapi-typescript` để tự động chuyển đổi OpenAPI Specification 3.1 (`http://127.0.0.1:8001/api/v1/openapi.json`) thành tệp TypeScript definition (`frontend/src/types/api.generated.d.ts`). Xây dựng module type helper tập trung (`frontend/src/types/api.ts`) cung cấp `Schema<T>`, `ApiPaths`, và các tiện ích tương thích với chuẩn envelope `ApiResponse[T]` (Hiến chương Điều V). Triển khai cấu hình tự động hóa trong `package.json` và root `Makefile`, đồng thời tiến hành thử nghiệm mẫu (Pilot) chuyển đổi các types của module `Homework` sang schema tự sinh để chứng minh tính khả thi và đảm bảo zero regression.

## Technical Context

**Language/Version**: Python 3.12 (FastAPI), TypeScript 5.9 (React 19 + Vite 7)  
**Primary Dependencies**: `openapi-typescript` (devDependency), FastAPI, Pydantic V2, Dishka, Axios, TanStack Query V5  
**Storage**: N/A (Build Tooling, Static Typing & Compile-Time Contracts)  
**Testing**: `npm run build`, `npm run lint`, `tsc --noEmit`, `pytest`  
**Target Platform**: Node.js Development Environment & Browser Web Client  
**Project Type**: Full-stack Web Application (FastAPI backend + React frontend)  
**Performance Goals**: Quá trình sinh type hoàn tất < 5s khi backend server đang chạy; 0 KB bundle size overhead tại runtime  
**Constraints**: Tuân thủ nghiêm ngặt Hiến chương dự án (Điều V: `ApiResponse[T]` envelope; Điều X: Single Source of Truth; Điều XV: Unified Client Networking)  
**Scale/Scope**: Tác động vào frontend build tools, thư mục `frontend/src/types/`, root `Makefile`, và refactor mẫu các types trong `frontend/src/features/homework/`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Principle I: Clean Architecture & Practical DDD Boundaries**: Tầng Presentation và DTO của backend được giữ nguyên vẹn; frontend sinh type trực tiếp từ hợp đồng DTO, không can thiệp vào tầng domain/use case.
- [x] **Principle V: API Backward Compatibility & Non-Null Contract DTOs**: Hỗ trợ đầy đủ phong bì chuẩn `ApiResponse[T]` thông qua helper `ApiResponseBody` và `Schema<T>`, đảm bảo tính toàn vẹn và non-null contracts cho frontend.
- [x] **Principle VII: Strict Single-Responsibility Use Cases**: Không làm thay đổi hay xáo trộn cấu trúc các Use Case hiện hữu.
- [x] **Principle X: Zero Redundant Backward Compatibility & Contextual Field Ownership**: Loại bỏ việc gõ tay lặp lại các interface DTO trong frontend, chuyển dần toàn bộ các kiểu dữ liệu phản hồi về nguồn sự thật duy nhất từ backend schema.
- [x] **Principle XV: Unified Client Networking**: Tương thích hoàn hảo với `axiosInstance`, cung cấp type an toàn cho các generic request/response của axios client.

## Project Structure

### Documentation (this feature)

```text
specs/054-openapi-type-generation/
├── plan.md              # File này (/speckit-plan output)
├── research.md          # Kết quả nghiên cứu công cụ & phương án (/speckit-plan Phase 0)
├── data-model.md        # Mô hình kiểu dữ liệu ánh xạ (/speckit-plan Phase 1)
├── quickstart.md        # Hướng dẫn chạy và xác minh (/speckit-plan Phase 1)
├── contracts/           # Hợp đồng giao tiếp & helpers (/speckit-plan Phase 1)
│   ├── openapi_typegen_contract.md
│   └── type_helper_contract.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Kế hoạch công việc cụ thể (/speckit-tasks output)
```

### Source Code (repository root)

```text
frontend/
├── package.json                         # Bổ sung devDependency openapi-typescript & script generate:api
├── src/
│   ├── types/
│   │   ├── api.generated.d.ts           # File type definition tự sinh từ openapi.json
│   │   ├── api.types.ts                 # Cấu trúc ApiResponse<T> & PaginationMeta hiện hữu
│   │   ├── api.ts                       # Module type helper: Schema<T>, ApiPaths, ApiResponseBody
│   │   └── index.ts                     # Re-export các helper từ api.ts
│   └── features/homework/
│       ├── types/homework.types.ts      # Di chuyển interface viết tay sang Schema<"...">
│       └── services/homework.service.ts # Sử dụng types chuẩn hóa
Makefile                                 # Thêm target frontend-generate-api
```

**Structure Decision**: Ứng dụng Web full-stack (FastAPI Backend + React Frontend Monorepo), tích hợp typegen vào pipeline phát triển cục bộ và CI.

## Complexity Tracking

*Không có vi phạm Constitution nào cần giải trình.*
