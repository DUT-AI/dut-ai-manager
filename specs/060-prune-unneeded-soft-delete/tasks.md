# Tasks: Lược bỏ is_deleted trên các Model không cần thiết (Prune Unneeded Soft Delete)

**Input**: Design documents from `specs/060-prune-unneeded-soft-delete/`
**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Có thể thực hiện song song (khác file, không phụ thuộc)
- **[Story]**: Gắn với User Story (US1: Meetings/Participants, US2: Homeworks/Assignees, US3: Team/Notifications/Others, MIGRATION: Dọn dẹp DB)

---

## Phase 1: Setup & Base Infrastructure

**Mục đích**: Bổ sung mixin kiến trúc dùng chung không có soft delete.

- [x] T001 Thêm `SQLAlchemyAuditTimestampMixin` vào `backend/app/shared/infrastructure/base_model.py` (kết hợp `SQLAlchemyTimestampOnlyMixin` và `SQLAlchemyAuditMixin`, không có `is_deleted`).
- [x] T002 [P] Tạo unit test kiểm thử hành vi độc lập của `SQLAlchemyAuditTimestampMixin` trong `backend/tests/unit/test_audit_timestamp_mixin.py`.

---

## Phase 2: Database Migration (Foundational)

**Mục đích**: Tạo migration Alembic dọn dẹp các bản ghi xóa mềm lịch sử và loại bỏ cột `is_deleted` trên database.

- [x] T003 Viết file migration Alembic `backend/alembic/versions/043_prune_unneeded_soft_delete.py`:
  - Dọn sạch cascade các bản ghi `is_deleted = true` của `meetings` (44), `meeting_participants` (64), `homeworks` (8), `team_members` (19).
  - Dọn sạch 2 cột rác lịch sử `homeworks.homework_slug` và `homeworks.game_slug`.
  - Thực hiện `op.drop_column('...', 'is_deleted')` trên: `meetings`, `meeting_participants`, `homeworks`, `homework_assignees`, `team_members`, `user_roles`, `notifications`, `push_subscriptions`, `permissions`, `roles`, `teams`, `monthly_user_stats`, `invoice_items`, `cleaning_duties`.
- [x] T004 Chạy thử nghiệm migration `uv run alembic upgrade head` trên môi trường DEV và xác nhận schema sạch sẽ.

---

## Phase 3: User Story 1 - Hard Delete cho Meeting & MeetingParticipant (Priority: P1) 🎯 MVP

**Mục tiêu**: Loại bỏ `is_deleted` khỏi module Meeting, chuyển sang xóa cứng vật lý và xóa bỏ các filter `WHERE is_deleted = false`.

### Implementation for US1
- [x] T005 [P] [US1] Cập nhật Domain Entities `Meeting` và `MeetingParticipant` trong `backend/app/meeting/domain/entity.py` và `participant.py`: Bỏ thuộc tính `is_deleted`.
- [x] T006 [P] [US1] Cập nhật ORM Models `Meeting`, `MeetingParticipant`, `MeetingEvaluation`, `MeetingOverallEvaluation` trong `backend/app/meeting/infrastructure/model.py`: Chuyển sang kế thừa `SQLAlchemyAuditTimestampMixin` / `SQLAlchemyTimestampOnlyMixin` và loại bỏ `is_deleted` trong `to_entity()` / `from_entity()`.
- [x] T007 [US1] Rà soát và gỡ bỏ các điều kiện `where(is_deleted == False)` trong `MeetingRepository` và `ParticipantRepository` ([backend/app/meeting/infrastructure/repositories/](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/meeting/infrastructure/repositories/)).
- [x] T008 [US1] Chạy kiểm thử module Meeting: `uv run pytest tests/unit/test_meeting_domain.py tests/unit/test_meeting_use_cases.py tests/api/test_meeting_api.py`.

---

## Phase 4: User Story 2 - Hard Delete cho Homework & Assignee (Priority: P2)

**Mục tiêu**: Loại bỏ `is_deleted` khỏi module Homework, chuyển sang xóa cứng và cascade sạch assignees/submissions.

### Implementation for US2
- [x] T009 [P] [US2] Cập nhật Domain Entities `Homework` và `HomeworkAssignee` trong `backend/app/homework/domain/entity.py`: Bỏ thuộc tính `is_deleted`.
- [x] T010 [P] [US2] Cập nhật ORM Models `HomeworkModel` và `HomeworkAssigneeModel` trong `backend/app/homework/infrastructure/model.py`: Chuyển sang kế thừa `SQLAlchemyAuditTimestampMixin` / `SQLAlchemyTimestampOnlyMixin` và loại bỏ `is_deleted`.
- [x] T011 [US2] Rà soát và gỡ bỏ các điều kiện `where(is_deleted == False)` trong `HomeworkRepository` và các use case liên quan.
- [x] T012 [US2] Chạy kiểm thử module Homework: `uv run pytest tests/unit/test_homework_validation.py tests/unit/test_homework_checker.py tests/api/test_homework_api.py`.

---

## Phase 5: User Story 3 - Hard Delete cho Team, Notifications & Các Bảng Phụ trợ (Priority: P3)

**Mục tiêu**: Loại bỏ `is_deleted` trên `team_members`, `notifications`, `push_subscriptions`, `user_roles`, `invoice_items`, `cleaning_duties`.

### Implementation for US3
- [x] T013 [P] [US3] Cập nhật `TeamMember` và `Team` trong `backend/app/team/`: Domain entity, ORM Model và Repository chuyển sang hard delete.
- [x] T014 [P] [US3] Cập nhật `NotificationModel` và `PushSubscriptionModel` trong `backend/app/reminder/infrastructure/model.py`: Chuyển sang `SQLAlchemyTimestampOnlyMixin`, bỏ `is_deleted`.
- [x] T015 [P] [US3] Cập nhật `CleaningDutyModel` trong `backend/app/duty/infrastructure/model.py`: Chuyển sang `SQLAlchemyAuditTimestampMixin`, bỏ `is_deleted`.
- [x] T016 [P] [US3] Cập nhật `InvoiceItemModel` trong `backend/app/billing/infrastructure/model.py`: Chuyển sang `SQLAlchemyTimestampOnlyMixin`, bỏ `is_deleted`.
- [x] T017 [P] [US3] Cập nhật `RoleModel`, `PermissionModel`, `UserRoleModel` trong `backend/app/rbac/infrastructure/model.py`: Bỏ `is_deleted`.
- [x] T018 [P] [US3] Cập nhật `MonthlyUserStatsModel` trong `backend/app/user/infrastructure/model.py`: Bỏ `is_deleted`.

---

## Phase 6: Polish & Verification

**Mục tiêu**: Kiểm tra hồi quy toàn diện trên toàn bộ hệ thống.

- [x] T019 Chạy `alembic check` để đảm bảo 100% ORM Models khớp với Database Schema, không còn bất kỳ diff lệch nào.
- [x] T020 Chạy toàn bộ test suite: `uv run pytest` (Đảm bảo 418/418 tests PASSED).
