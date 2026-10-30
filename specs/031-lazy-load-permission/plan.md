# Implementation Plan: Kịch bản A - Tối ưu danh sách PermissionRequest & API Detail riêng biệt

- **Branch**: `031-lazy-load-permission`
- **Spec**: `specs/031-lazy-load-permission/spec.md`

## 1. Kiến trúc & Thiết kế (Architecture & DDD)
Tuân thủ **Hiến pháp DUT AI Manager Constitution v1.6.0**:
- **Principle I (Clean Architecture & Practical DDD Boundaries)**:
  - Danh sách `PermissionRequest` chỉ mang thông tin của Aggregate `PermissionRequest` + `creator: UserRef`.
  - Không nhúng Aggregate khác vào list query.
- **Principle VII (Strict Single-Responsibility Use Cases)**:
  - Tạo file riêng: `backend/app/permission_request/application/get_permission_request_detail_use_case.py` với duy nhất method `execute(request_id: int)`.
  - Re-export trong `application/__init__.py`.
- **Principle II (Dependency Injection with Dishka)**:
  - Đăng ký `GetPermissionRequestDetailUseCase` trong `backend/app/permission_request/providers.py`.
- **Principle V (API Backward Compatibility & Non-Null Contracts)**:
  - `PermissionRequestResponse` (dành cho list): không còn chứa `homework`, `meeting`, `old_meeting`.
  - `PermissionRequestDetailResponse`: kế thừa hoặc mở rộng chứa `homework: HomeworkResponse | None`, `meeting: MeetingResponse | None`, `old_meeting: MeetingResponse | None`.

---

## 2. Các bước triển khai chi tiết

### Phase 1: Backend DTOs & Schemas
1. Trong `backend/app/permission_request/schemas.py`:
   - `PermissionRequestResponse`: Bỏ các field `homework`, `meeting`, `old_meeting`. Giữ `id, category, note, homework_id, meeting_id, old_meeting_id, start_time, created_at, updated_at, creator, updater, owner`.
   - Tạo class mới `PermissionRequestDetailResponse(PermissionRequestResponse)`:
     ```python
     class PermissionRequestDetailResponse(PermissionRequestResponse):
         homework: HomeworkResponse | None = None
         meeting: MeetingResponse | None = None
         old_meeting: MeetingResponse | None = None
     ```

### Phase 2: Repository Refactor & Add Detail Query
1. Trong `backend/app/permission_request/infrastructure/repository.py`:
   - Xóa bỏ tất cả `joinedload(ORMModel.homework)` và `joinedload(ORMModel.meeting)` / `joinedload(ORMModel.old_meeting)` khỏi các hàm:
     - `get_paged`
     - `get_by_date`
     - `get_by_month`
     - `get_by_user`
   - Viết method mới:
     ```python
     def get_detail_by_id(self, request_id: int) -> ORMModel | None:
         stmt = (
             select(ORMModel)
             .options(
                 joinedload(ORMModel.creator),
                 joinedload(ORMModel.updater),
                 joinedload(ORMModel.homework).noload(HomeworkModel.assignees),
                 joinedload(ORMModel.homework).noload(HomeworkModel.submissions),
                 joinedload(ORMModel.meeting),
                 joinedload(ORMModel.old_meeting),
             )
             .where(ORMModel.id == request_id)
         )
         return self.session.scalars(stmt).unique().first()
     ```

### Phase 3: Application Layer & API Controller
1. Tạo `backend/app/permission_request/application/get_permission_request_detail_use_case.py`:
   - Inject `PermissionRequestRepository`.
   - Method `execute(self, request_id: int) -> PermissionRequestDetailResponse`: lấy ORM model qua `get_detail_by_id`, nếu không thấy thì raise 404, trả về DTO.
2. Cập nhật `backend/app/permission_request/providers.py`:
   - Register `GetPermissionRequestDetailUseCase`.
3. Cập nhật `backend/app/permission_request/controller.py`:
   - Thêm route `GET /{request_id}` trả về `ApiResponse[PermissionRequestDetailResponse]`.

### Phase 4: Frontend Service, Hook & UI Components
1. `frontend/src/features/rbac/services/permission.service.ts`:
   - Thêm phương thức `getById(id: number): Promise<ApiResponse<PermissionRequestDetailResponse>>`.
2. Tạo hook `usePermissionDetail(id: number | null)` trong `frontend/src/features/rbac/hooks/usePermissions.ts` (hoặc file hook tương ứng).
3. Cập nhật `frontend/src/features/rbac/components/permissions/PermissionTable.tsx`:
   - Cột mục tiêu hiển thị nhẹ gọn theo ID:
     - `POSTPONE`: `#Bài tập ${record.homework_id}`
     - `ABSENCE` / `LATE`: `#Buổi học ${record.meeting_id}`
     - `CHANGE_MEETING`: `#Buổi ${record.old_meeting_id || 'Mới'} ➔ #${record.meeting_id}`
4. Cập nhật `frontend/src/features/rbac/components/permissions/PermissionDetailDrawer.tsx`:
   - Nhận `requestId: number | null` (hoặc `item: PermissionRequestResponse | null`).
   - Dùng hook `usePermissionDetail` để load chi tiết từ API với spinner loading khi đang fetch. Hiển thị thông tin `detailData.homework.title`, `detailData.meeting.title`, v.v.

### Phase 5: Testing & Verification
1. `uv run --directory backend pytest tests/unit/`
2. `uv run --directory backend ruff check app/permission_request/`
3. `npm --prefix frontend run build`
