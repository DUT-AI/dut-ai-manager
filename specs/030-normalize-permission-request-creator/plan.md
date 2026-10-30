# Implementation Plan: Chuẩn hóa người tạo (Creator/Owner) trong PermissionRequest

- **Branch**: `030-normalize-permission-request-creator`
- **Feature Directory**: `specs/030-normalize-permission-request-creator`
- **Spec**: `specs/030-normalize-permission-request-creator/spec.md`

## 1. Executive Summary

Trong `PermissionRequest` (`backend/app/permission_request`), bảng database chỉ có cột `created_by` và `updated_by`. Tuy nhiên, mã nguồn trước đây đang duy trì đồng thời 2 trường `owner: UserRef` và `creator: UserRef`. Cả hai trường đều trỏ vào cùng một đối tượng người dùng `created_by`. 
Việc này sinh ra quan hệ kép (`overlaps="creator"`, `overlaps="user"`) trong ORM Model, tốn công mapping kép trong `to_entity()`, và gây nhầm lẫn về mặt ngữ nghĩa miền (Domain semantics).

Kế hoạch này thực hiện chuẩn hóa:
- **Tên đại diện duy nhất**: Thống nhất dùng trường **`creator: UserRef | None`** (hoặc `creator` làm nguồn chân lý duy nhất đại diện cho người tạo đơn / chủ đơn).
- **Tránh breaking change cho Frontend**: 
  - Trong Pydantic Response Schema (`PermissionRequestResponse`): `creator: UserRef | None`. Để đảm bảo tương thích 100% với Frontend đang đọc `record.owner`, cung cấp một computed field hoặc alias `owner: UserRef | None = Field(default=None)` tự động gán bằng `creator`.
  - Đồng thời cập nhật các vị trí Frontend đọc `record.owner` chuyển sang ưu tiên `record.creator || record.owner` để chuẩn hóa hoàn toàn theo thời gian (tuân thủ Nguyên tắc X của Hiến pháp: Refactor Call Sites Directly).
- **Xóa bỏ quan hệ kép trong ORM Model**: Xóa bỏ `user` relationship thừa trong `PermissionRequest` ORM Model, chỉ giữ một relationship `creator` duy nhất liên kết với `created_by`.

---

## 2. Technical Context & Constitution Check

### A. Principle I (Clean Architecture & Practical DDD)
- **Domain Layer (`domain/entity.py`)**: `PermissionRequest` chỉ giữ:
  ```python
  creator: UserRef | None = None
  updater: UserRef | None = None
  ```
  Xóa hoàn toàn `owner: UserRef | None` khỏi Domain Entity.
- **Infrastructure Layer (`infrastructure/model.py`)**:
  - Xóa relationship `user` thừa.
  - Xóa bỏ các thuộc tính `overlaps="creator"` và `overlaps="user"`.
  - Giữ lại relationship duy nhất:
    ```python
    creator: Mapped["UserModel | None"] = relationship(
        foreign_keys="PermissionRequest.created_by",
    )
    ```
  - Trong `to_entity()`: Chỉ tạo `creator_ref` và `updater_ref`.
- **Presentation Layer (`schemas.py`)**:
  - Cập nhật `PermissionRequestResponse`:
    ```python
    creator: UserRef | None = None
    updater: UserRef | None = None
    ```
    Bổ sung `@computed_field` hoặc field `owner` serialize từ `creator` để đảm bảo API contract không bị gãy trên mọi client cũ.

### B. Principle X (Zero Redundant Backward Compatibility & Refactor Call Sites Directly)
- Cập nhật các file Frontend tại `frontend/src/features/rbac/components/permissions/`:
  - `PermissionTable.tsx`: đổi `record.owner` thành `record.creator || record.owner`.
  - `PermissionMobileList.tsx`: đổi `record.owner` thành `record.creator || record.owner`.
  - `PermissionDetailDrawer.tsx`: thống nhất hiển thị thông tin người tạo từ `creator`.

---

## 3. Step-by-Step Implementation Outline

### Bước 1: Refactor Domain Entity (`backend/app/permission_request/domain/entity.py`)
- Xóa trường `owner: UserRef | None = None`.
- Giữ lại `creator: UserRef | None = None` và `updater: UserRef | None = None`.

### Bước 2: Refactor Infrastructure Model (`backend/app/permission_request/infrastructure/model.py`)
- Xóa relationship `user: Mapped["UserModel"]`.
- Giữ relationship `creator`:
  ```python
  creator: Mapped["UserModel | None"] = relationship(
      foreign_keys="PermissionRequest.created_by",
  )
  ```
- Cập nhật `to_entity()`:
  - Chỉ trích xuất `creator_ref` từ `self.creator` (kiểm tra `if "creator" in self.__dict__ and self.creator:`).
  - Trả về entity với `creator=creator_ref, updater=updater_ref`.
- Cập nhật Repository nếu có `joinedload(ORMModel.user)` $\rightarrow$ đổi thành `joinedload(ORMModel.creator)`.

### Bước 3: Cập nhật Repository (`backend/app/permission_request/infrastructure/repository.py`)
- Thay đổi `joinedload(ORMModel.user)` $\rightarrow$ `joinedload(ORMModel.creator)` tại 4 hàm truy vấn (`get_paged`, `get_by_date`, `get_by_month`, `get_by_user`).

### Bước 4: Cập nhật API Schema (`backend/app/permission_request/schemas.py`)
- Cấu hình `PermissionRequestResponse`:
  - `creator: UserRef | None = None`
  - `@computed_field` hoặc property `owner: UserRef | None`: trả về `self.creator` để giữ tương thích ngược 100% cho mọi client.

### Bước 5: Cập nhật Frontend Call Sites (`frontend/src/features/rbac/components/permissions/`)
- Cập nhật `PermissionTable.tsx`, `PermissionMobileList.tsx`, `PermissionDetailDrawer.tsx` để đọc `record.creator || record.owner`.

### Bước 6: Verification & Testing
- Chạy `uv run --directory backend pytest tests/unit/` (yêu cầu 161/161 pass).
- Chạy `uv run --directory backend ruff check app/permission_request/`.
- Chạy `npm run build` trên thư mục `frontend/` để đảm bảo zero TypeScript error.
