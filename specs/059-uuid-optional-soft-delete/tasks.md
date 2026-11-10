# Tasks: Tách biệt Soft Delete và Hỗ trợ Khóa chính UUID cho Domain Model

**Input**: Design documents from `/specs/059-uuid-optional-soft-delete/`  
**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`  
**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description with file path`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)

---

## Phase 1: Setup & Foundational Prerequisites

**Purpose**: Xây dựng thuật toán sinh mã UUIDv7 chuẩn RFC 9562 tại tầng Domain dùng chung.

- [x] T001 [P] Implement RFC 9562 compliant `uuid7()` generator using Python standard library in `backend/app/shared/domain/uuid_utils.py`.
- [x] T002 [P] Implement unit tests verifying UUIDv7 version, variant, and time-ordering in `backend/tests/unit/test_uuid_and_optional_soft_delete.py`.

---

## Phase 2: User Story 1 - Flexible UUID Primary Key Support (Priority: P1) 🎯 MVP

**Goal**: Hỗ trợ UUIDv7 làm khóa chính cho các Domain Entity và ORM Model mới, tích hợp với `BaseRepository` để tìm kiếm và thêm mới bản ghi theo UUID mà không gây xung đột với các model dùng `int` ID cũ.

**Independent Test**: Tạo một model và entity mẫu dùng khóa chính UUIDv7, thêm vào database và gọi `repository.get_by_id(uuid)` trả về đúng entity.

### Tests for User Story 1
- [x] T003 [P] [US1] Add unit tests for UUIDv7 entity creation, persistence, and `get_by_id(uuid)` in `backend/tests/unit/test_uuid_and_optional_soft_delete.py`.

### Implementation for User Story 1
- [x] T004 [P] [US1] Implement `BaseGenericEntity[TId]` and `BaseUuidEntity` in `backend/app/shared/domain/base_entity.py`.
- [x] T005 [P] [US1] Implement `SQLAlchemyUuidPrimaryKeyMixin` and `SQLAlchemyIntPrimaryKeyMixin` in `backend/app/shared/infrastructure/base_model.py`.
- [x] T006 [US1] Update `BaseRepository.get_by_id` to accept `id: int | UUID | str` in `backend/app/shared/infrastructure/base_repository.py`.

**Checkpoint**: User Story 1 hoàn thành - Các model mới có thể sử dụng UUIDv7 làm khóa chính độc lập.

---

## Phase 3: User Story 2 - Decoupled & Optional Soft-Deletion (Priority: P2)

**Goal**: Tách biệt `is_deleted` thành mixin tùy chọn (opt-in), nâng cấp `BaseRepository` tự động kiểm tra `is_deleted` và phân tách rạch ròi 2 phương thức `soft_delete()` và `hard_delete()`.

**Independent Test**: Tạo một model không có `is_deleted` và một model có `is_deleted`. Xác nhận model không có `is_deleted` không phát sinh `WHERE is_deleted = false`, gọi `soft_delete()` báo lỗi `NotImplementedError`, và gọi `hard_delete()` xóa vĩnh viễn bản ghi.

### Tests for User Story 2
- [x] T007 [P] [US2] Add unit tests for queries on non-soft-delete models, `soft_delete()` failure on non-soft-delete models, and `hard_delete()` physical deletion in `backend/tests/unit/test_uuid_and_optional_soft_delete.py`.

### Implementation for User Story 2
- [x] T008 [P] [US2] Decouple `SQLAlchemySoftDeleteMixin` and `SQLAlchemyAuditMixin` from `SQLAlchemyTimestampMixin` in `backend/app/shared/infrastructure/base_model.py`.
- [x] T009 [P] [US2] Implement `SoftDeleteEntityMixin` and `AuditEntityMixin` in `backend/app/shared/domain/base_entity.py`.
- [x] T010 [US2] Update `BaseRepository.get_one`, `get_all`, and `get_paged` to dynamically check `hasattr(self.model, "is_deleted")` before applying `where(self.model.is_deleted == deleted)` in `backend/app/shared/infrastructure/base_repository.py`.
- [x] T011 [US2] Implement explicit `soft_delete(id_or_entity)` (raising `NotImplementedError` if model lacks `is_deleted`) and `hard_delete(id_or_entity)` in `backend/app/shared/infrastructure/base_repository.py`.

**Checkpoint**: User Story 2 hoàn thành - Model mới có thể lựa chọn có hoặc không có xóa mềm, và hành vi xóa được phân tách rạch ròi.

---

## Phase 4: User Story 3 - Composable Architecture & Backward Compatibility (Priority: P3)

**Goal**: Đảm bảo toàn bộ các class và mixin tương thích ngược 100% với các domain hiện có, cung cấp `SQLAlchemyFullAuditMixin` và `BaseEntity` kết hợp sẵn.

**Independent Test**: Chạy các test case với các entity và model kế thừa `BaseEntity` và `SQLAlchemyTimestampMixin` cũ, bảo đảm không có lỗi breaking changes.

- [x] T012 [P] [US3] Recompose `BaseEntity` in `backend/app/shared/domain/base_entity.py` using `BaseGenericEntity[int]`, `AuditEntityMixin`, and `SoftDeleteEntityMixin` to preserve 100% field signature.
- [x] T013 [P] [US3] Provide `SQLAlchemyFullAuditMixin` and ensure `SQLAlchemyTimestampMixin` preserves compatibility for legacy models in `backend/app/shared/infrastructure/base_model.py`.
- [x] T014 [US3] Add backward compatibility regression unit tests for legacy entities and models in `backend/tests/unit/test_uuid_and_optional_soft_delete.py`.

---

## Phase 5: Verification & Zero-Regression Validation

**Purpose**: Chạy toàn bộ test suites và kiểm thử hồi quy trên toàn bộ hệ thống backend.

- [x] T015 Run specialized unit test suite `uv run pytest tests/unit/test_uuid_and_optional_soft_delete.py` in `backend/`.
- [x] T016 Run full backend test suite `uv run pytest` in `backend/` to ensure zero regressions across all domain modules (User, Meeting, Homework, PermissionRequest, etc.).

---

## Dependencies & Execution Order

### Phase Dependencies
- **Phase 1 (Setup)**: Không có phụ thuộc, thực hiện đầu tiên.
- **Phase 2 (US1 - UUID PK)**: Phụ thuộc vào Phase 1 (`uuid_utils.py`).
- **Phase 3 (US2 - Optional Soft Delete)**: Phụ thuộc vào Phase 2 (nâng cấp BaseRepository).
- **Phase 4 (US3 - Composable & Legacy Compatibility)**: Phụ thuộc vào Phase 2 & 3.
- **Phase 5 (Verification)**: Chạy sau khi hoàn thành Phase 2, 3, 4.

### Parallel Opportunities
- T001 và T002 có thể chạy song song.
- T004 và T005 có thể chỉnh sửa song song (tầng domain vs tầng infrastructure).
- T008 và T009 có thể chỉnh sửa song song.

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Hoàn thành Phase 1 (`uuid_utils.py`).
2. Hoàn thành Phase 2 (User Story 1 - Khóa chính UUIDv7).
3. Chạy test xác nhận MVP: Tạo và truy vấn bản ghi bằng UUIDv7 thành công.

### Incremental Delivery
1. Giao Phase 1 + 2: Hỗ trợ UUIDv7 làm khóa chính.
2. Giao Phase 3: Tách rời xóa mềm và nâng cấp BaseRepository với `soft_delete()` / `hard_delete()`.
3. Giao Phase 4 + 5: Đảm bảo tương thích ngược 100% và chạy toàn bộ test hồi quy.
