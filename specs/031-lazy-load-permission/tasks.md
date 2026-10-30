# Tasks: Kịch bản A - Tối ưu danh sách PermissionRequest & API Detail riêng biệt

**Input**: Design documents from `specs/031-lazy-load-permission/`  
**Prerequisites**: `plan.md`, `spec.md`, `constitution.md`

## Phase 1: Backend DTO & Repository Optimization (Foundational)

- [x] T001 [Backend] Cập nhật schemas trong `backend/app/permission_request/schemas.py`:
  - Trong `PermissionRequestResponse`: Bỏ các field `homework`, `meeting`, `old_meeting`.
  - Tạo mới `PermissionRequestDetailResponse(PermissionRequestResponse)`: Thêm `homework: HomeworkResponse | None = None`, `meeting: MeetingResponse | None = None`, `old_meeting: MeetingResponse | None = None`.
- [x] T002 [Backend] Tối ưu Repository trong `backend/app/permission_request/infrastructure/repository.py`:
  - Bỏ toàn bộ `joinedload(ORMModel.homework)`, `joinedload(ORMModel.meeting)`, `joinedload(ORMModel.old_meeting)` khỏi các hàm danh sách (`get_paged`, `get_by_date`, `get_by_month`, `get_by_user`).
  - Thêm phương thức `get_detail_by_id(self, request_id: int) -> PermissionRequestDetailResponse | None` thực hiện query có eager load đầy đủ các quan hệ.

---

## Phase 2: Application Layer & API Controller

- [x] T003 [Backend] Tạo Use Case `GetPermissionRequestDetailUseCase` trong `backend/app/permission_request/application/get_permission_request_detail_use_case.py`.
- [x] T004 [Backend] Re-export Use Case trong `backend/app/permission_request/application/__init__.py` và đăng ký provider trong `backend/app/permission_request/providers.py`.
- [x] T005 [Backend] Thêm endpoint `GET /api/v1/permissions/{request_id}` trong `backend/app/permission_request/controller.py` trả về `ApiResponse[PermissionRequestDetailResponse]`.

---

## Phase 3: Frontend Service, Hook & UI Optimization

- [x] T006 [Frontend] Cập nhật `frontend/src/features/rbac/services/permission.service.ts`:
  - Thêm hàm `getById(id: number): Promise<ApiResponse<PermissionRequestDetailResponse>>`.
- [x] T007 [Frontend] Thêm hook `usePermissionDetail(id: number | null, enabled: boolean)` trong `frontend/src/features/rbac/hooks/usePermissions.ts`.
- [x] T008 [Frontend] Cập nhật `frontend/src/features/rbac/components/permissions/PermissionTable.tsx`:
  - Cột "Mục tiêu" hiển thị mã định danh gọn nhẹ theo ID khi chưa có detail (`#Bài tập ${record.homework_id}`, `#Buổi học ${record.meeting_id}`).
- [x] T009 [Frontend] Cập nhật `frontend/src/features/rbac/components/permissions/PermissionDetailDrawer.tsx`:
  - Gọi hook `usePermissionDetail(item?.id)` để fetch chi tiết khi Drawer mở; hiển thị Spin loader khi đang fetch và render dữ liệu chi tiết đầy đủ khi fetch xong.

---

## Phase 4: Verification & Test Suite

- [x] T010 Chạy benchmark kiểm tra thời gian query danh sách `get_paged` (< 30ms).
- [x] T011 Chạy `uv run --directory backend pytest tests/unit/`.
- [x] T012 Chạy `uv run --directory backend ruff check app/permission_request/`.
- [x] T013 Chạy `npm --prefix frontend run build` kiểm tra TypeScript.
