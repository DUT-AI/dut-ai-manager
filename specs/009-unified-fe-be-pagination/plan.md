# Implementation Plan: Đồng Nhất Kiến Trúc Phân Trang Giữa Frontend và Backend (Unified FE-BE Pagination)

**Branch**: `009-unified-fe-be-pagination` | **Date**: 2026-10-10 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/009-unified-fe-be-pagination/spec.md`

---

## Summary

Thiết kế và triển khai đồng nhất kiến trúc phân trang 2 chiều giữa Frontend (Web Admin), Backend (FastAPI) và Zalo Mini App:
1. **Backend Core & Presentation Layer**:
   - Mở rộng DTO `ApiResponse` trong `app.shared.application.response` với trường `pagination: PaginationMeta | None = None`. Giữ nguyên `data: list[T]` để tương thích ngược 100% với các client cũ (đặc biệt là Zalo Mini App).
   - Chuẩn hoá tham số đầu vào sang `page: int = 1, page_size: int = 20` thông qua FastAPI dependency `PaginationParams`. Loại bỏ hoàn toàn các tham số `skip` và `limit` trên toàn hệ thống.
   - Cung cấp endpoint rút gọn `/users/options`, `/teams/options` cho các dropdown Form Select mà không bị giới hạn cứng 20 bản ghi.
2. **Backend Infrastructure Layer**:
   - Bổ sung phương thức dùng chung `get_paged(...)` trong `BaseRepository`: tự động phân tách và tối ưu câu lệnh `COUNT` (loại bỏ `ORDER BY` và eager joins) độc lập với câu lệnh `SELECT` phân trang.
3. **Frontend Layer**:
   - Cập nhật định nghĩa TypeScript `ApiResponse<T>` và `PaginationMeta` trong `frontend/src/types/api.types.ts`.
   - Xây dựng Custom Hook `useTablePagination` đồng bộ 2 chiều với URL Search Parameters (`useSearchParams`), tự động cấu hình Ant Design `Table.pagination` tuân thủ Constitution Điều VIII (`pageSize >= 20`, `pageSizeOptions`, `showSizeChanger`, `showTotal`).
   - Cập nhật các API services và React Query hooks sang chuẩn `(page, page_size)`.
4. **Zalo Mini App Layer**:
   - Cập nhật các API service trong `zalo-mini-app/` từ `skip`/`limit` sang `page`/`page_size`.

---

## Technical Context

**Language/Version**: Python 3.12 (Backend), TypeScript 5.x (Frontend Web & Zalo Mini App)  
**Primary Dependencies**:
- Backend: FastAPI, SQLAlchemy 2.0, Dishka (DI), Pydantic V2, Alembic
- Frontend: React 18/19, Ant Design 5.x, @tanstack/react-query 5.x, react-router-dom 6.x, Axios
- Zalo Mini App: Zalo Mini App SDK, Axios  
**Storage**: PostgreSQL (Production) / SQLite (In-Memory Testing)  
**Testing**: `pytest`, `pytest-asyncio` (Backend); `npm run build` & TypeScript compiler check (Frontend)  
**Target Platform**: Web Admin Dashboard, Zalo Mini App, Linux Server Docker  
**Project Type**: Full-stack Web Application / Monorepo REST API  
**Performance Goals**: Truy vấn `COUNT` tối ưu trong `BaseRepository` loại bỏ triệt để eager joins và sorting; độ trễ API phân trang $< 100\text{ ms}$ cho các bảng $> 50,000$ bản ghi  
**Constraints**:
- Tuân thủ Constitution Điều V: Envelope chuẩn `ApiResponse[T]`, Non-Null Contract DTO.
- Tuân thủ Constitution Điều VIII: Mọi bảng hiển thị phải có `defaultPageSize >= 20`, `pageSizeOptions: ['10', '20', '50', '100']`, `showSizeChanger: true`, `showTotal`.
- 100% test pass, 0 typecheck diagnostics (`make typecheck`, `npm run build`).  
**Scale/Scope**: ~12 controllers/repositories backend, 8 service hooks frontend, 1 hook mới, 4 service files Zalo Mini App.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

- [x] **I. Clean Architecture & Practical DDD Boundaries**: Phân tầng rành mạch: `PaginationParams` nằm ở Presentation, `PagedResult` nằm ở Application/Domain, `BaseRepository.get_paged` nằm ở Infrastructure.
- [x] **II. Dependency Injection with Dishka**: Các Use Cases xử lý phân trang tiếp tục được giải quyết qua Dishka providers và tiêm vào Controller bằng `FromDishka[...]`.
- [x] **V. API Backward Compatibility & Non-Null Contract DTOs**: `ApiResponse` giữ nguyên trường `data: list[T]` để các client cũ đọc mảng trực tiếp không bị vỡ; trường `pagination` là optional extension.
- [x] **VII. Single-Responsibility Use Cases**: Không gom nhóm bừa bãi; mỗi Use Case giữ đúng 1 nhiệm vụ.
- [x] **VIII. Frontend Component Modularity & Table Pagination**: Hook `useTablePagination` bảo đảm mọi bảng Ant Design đều cấu hình rõ ràng `pageSize >= 20`, `pageSizeOptions`, `showSizeChanger`, và `showTotal`.
- [x] **Zero Secret Leakage**: Không có secret mới nào được đưa vào code.

---

## Project Structure

### Documentation (this feature)

```text
specs/009-unified-fe-be-pagination/
├── spec.md              # Feature specification
├── plan.md              # Implementation plan (this file)
├── research.md          # Phase 0: Technical decisions & rationale
├── data-model.md        # Phase 1: Data structures & schemas
├── quickstart.md        # Phase 1: Verification scenarios & test guide
├── contracts/           # Phase 1: API Contracts
│   └── pagination-api-contract.md
└── tasks.md             # Phase 2: Actionable tasks (created via /speckit-tasks)
```

### Source Code Impacted

```text
backend/
├── app/
│   ├── shared/
│   │   ├── application/
│   │   │   ├── response.py                # Mở rộng ApiResponse, thêm PaginationMeta
│   │   │   ├── pagination.py              # Thêm PaginationParams dependency
│   │   │   └── query_support_utils.py     # Cập nhật build_query_support (page, page_size)
│   │   ├── domain/
│   │   │   └── query_support.py           # Cập nhật OffsetPaginationParams
│   │   └── infrastructure/
│   │       └── base_repository.py         # Bổ sung get_paged(...) tối ưu COUNT
│   ├── meeting/
│   │   ├── controller.py                  # Chuyển skip/limit sang PaginationParams
│   │   └── application/                   # Cập nhật get_meetings_use_case
│   ├── violation/
│   │   ├── controller.py                  # Chuyển skip/limit sang PaginationParams
│   │   └── application/                   # Cập nhật get_violations_use_case
│   ├── homework/
│   │   ├── controller.py                  # Chuyển skip/limit sang PaginationParams
│   │   └── application/                   # Cập nhật get_homeworks_use_case
│   ├── user/
│   │   ├── controller.py                  # Thêm phân trang cho list_users, thêm /users/options
│   │   └── application/                   # Cập nhật get_user_use_case
│   └── billing/team/rbac/                 # Cập nhật phân trang tương tự

frontend/
├── src/
│   ├── types/
│   │   └── api.types.ts                   # Thêm PaginationMeta, cập nhật ApiResponse<T>
│   ├── hooks/
│   │   └── useTablePagination.ts          # Custom hook đồng bộ URL và sinh Antd Table props
│   ├── features/
│   │   ├── meeting/
│   │   │   ├── services/meeting.service.ts
│   │   │   ├── hooks/useMeetings.ts
│   │   │   └── components/                # Áp dụng useTablePagination
│   │   ├── violations/
│   │   ├── homework/
│   │   └── users/

zalo-mini-app/
└── dut-manager/src/services/api/
    ├── meeting.service.ts                 # Chuyển skip/limit sang page/page_size
    ├── homework.service.ts
    ├── team.service.ts
    └── permission.service.ts
```

---

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Không có vi phạm | Thiết kế bám sát 100% Constitution của dự án | Không áp dụng |
