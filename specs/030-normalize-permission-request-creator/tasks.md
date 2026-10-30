# Tasks: Chuẩn hóa người tạo (Creator/Owner) trong PermissionRequest

**Input**: Design documents from `specs/030-normalize-permission-request-creator/`  
**Prerequisites**: `plan.md`, `spec.md`, `constitution.md`

## Organization:
- **Phase 1: Domain & Model Refactor (Foundational)**: Chuẩn hóa Entity và ORM Model của PermissionRequest.
- **Phase 2: Repository & Schema Refactor (Contract)**: Cập nhật eager-load trong Repository và Pydantic DTO tương thích.
- **Phase 3: Frontend Refactor (UI Normalization)**: Cập nhật các component giao diện hiển thị thông tin người tạo.
- **Phase 4: Verification & Test Suite**: Chạy toàn bộ test backend và build frontend.

---

## Phase 1: Domain & Model Refactor (Foundational)

**Purpose**: Loại bỏ thuộc tính dư thừa `owner` khỏi Domain Entity và dọn dẹp quan hệ kép trong ORM Model.

- [x] T001 [Domain] Cập nhật Domain Entity `PermissionRequest` trong `backend/app/permission_request/domain/entity.py`:
  - Xóa bỏ `owner: UserRef | None = None`.
  - Giữ lại `creator: UserRef | None = None` và `updater: UserRef | None = None`.
- [x] T002 [Model] Chuẩn hóa ORM Model `PermissionRequest` trong `backend/app/permission_request/infrastructure/model.py`:
  - Xóa bỏ relationship `user: Mapped["UserModel"]`.
  - Giữ lại relationship duy nhất: `creator: Mapped["UserModel | None"] = relationship(foreign_keys="PermissionRequest.created_by")`.
  - Xóa các tham số `overlaps="creator"` / `overlaps="user"`.
  - Trong `to_entity()`: Chỉ tạo `creator_ref` từ `self.creator` và gán vào `creator=creator_ref, updater=updater_ref`.

**Checkpoint**: Entity & ORM Model độc lập, không còn cảnh báo mapper overlaps và không còn thuộc tính `owner` ở tầng domain.

---

## Phase 2: Repository & Schema Refactor (Contract)

**Purpose**: Đảm bảo repository eager-load đúng relationship và DTO phản hồi an toàn cho client.

- [x] T003 [Repository] Cập nhật eager load trong `backend/app/permission_request/infrastructure/repository.py`:
  - Thay thế `joinedload(ORMModel.user)` bằng `joinedload(ORMModel.creator)` tại các hàm `get_paged`, `get_by_date`, `get_by_month`, `get_by_user`.
- [x] T004 [Schema] Cập nhật Pydantic Schema trong `backend/app/permission_request/schemas.py`:
  - Trong `PermissionRequestResponse`: Giữ `creator: UserRef | None = None`.
  - Cung cấp `@computed_field` hoặc field `owner` alias trỏ về `creator` để đảm bảo API contract backward-compatible 100% với các client chưa kịp nâng cấp.

**Checkpoint**: API `GET /api/v1/permissions` trả về đúng payload chứa `creator` và alias `owner`.

---

## Phase 3: Frontend Refactor (UI Normalization)

**Purpose**: Cập nhật trực tiếp các vị trí hiển thị người tạo trên giao diện Web Frontend.

- [x] T005 [P] [FE] Cập nhật `frontend/src/features/rbac/components/permissions/PermissionTable.tsx`:
  - Đổi hiển thị tên và avatar sang ưu tiên `record.creator?.name || record.owner?.name`.
- [x] T006 [P] [FE] Cập nhật `frontend/src/features/rbac/components/permissions/PermissionMobileList.tsx`:
  - Đổi hiển thị sang `record.creator?.name || record.owner?.name`.
- [x] T007 [P] [FE] Cập nhật `frontend/src/features/rbac/components/permissions/PermissionDetailDrawer.tsx`:
  - Đổi hiển thị phần thông tin người tạo sang `item.creator?.name || item.owner?.name`.

**Checkpoint**: Toàn bộ giao diện hiển thị người tạo trên danh sách và chi tiết đơn xin phép hoạt động mượt mà.

---

## Phase 4: Verification & Test Suite

**Purpose**: Kiểm thử toàn diện chất lượng mã nguồn.

- [x] T008 [Verification] Chạy Ruff linter trên backend:
  - `uv run --directory backend ruff check app/permission_request/`
- [x] T009 [Verification] Chạy toàn bộ Unit Test backend:
  - `uv run --directory backend pytest tests/unit/`
- [x] T010 [Verification] Kiểm tra build TypeScript Frontend:
  - `npm --prefix frontend run build`

---

## Dependencies & Execution Order
- T001, T002 $\rightarrow$ T003, T004 $\rightarrow$ T005, T006, T007 $\rightarrow$ T008, T009, T010.
