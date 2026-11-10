# Tasks: Bắt buộc chọn ca hiện tại và kiểm tra có mặt khi đổi buổi meeting

**Input**: Design documents from `/specs/058-require-current-meeting-for-change/`  
**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`  
**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)

---

## Phase 1: Setup & Foundational Prerequisites

**Purpose**: Cập nhật DTO Payload schema của tầng Domain.

- [x] T001 [US1] Update `ChangeMeetingPayload` in `backend/app/permission_request/domain/payloads.py` to make `old_meeting_id: int` mandatory (non-optional).

---

## Phase 2: User Story 1 - Backend Validation & Attendance Verification (Priority: P1) 🎯 MVP

**Goal**: Bắt buộc chọn ca hiện tại và kiểm tra người dùng có mặt trong danh sách tham gia của ca đó trước khi cho phép đổi ca.

### Tests for User Story 1
- [x] T002 [P] [US1] Update unit tests in `backend/tests/unit/test_change_meeting_permission_request.py` to assert rejection when `old_meeting_id` is missing or when user is not an active participant in `old_meeting_id`.
- [x] T003 [P] [US1] Update API integration tests in `backend/tests/api/test_change_meeting_api.py` to test validation errors for missing/invalid `old_meeting_id`.

### Implementation for User Story 1
- [x] T004 [US1] Update `ChangeMeetingStrategy.validate` in `backend/app/permission_request/application/strategies/change_meeting_strategy.py` to verify:
  - `old_meeting_id` is provided.
  - `old_meeting` exists via `meeting_repo.get_by_id(old_meeting_id)`.
  - `user_id` exists in `old_meeting.participants` with `is_deleted = False`.
  - Raise `HTTPException(400, "Bạn không có mặt trong danh sách tham gia của buổi sinh hoạt hiện tại đã chọn")` if not a participant.
- [x] T005 [US1] Run unit and integration tests via `uv run pytest tests/unit/test_change_meeting_permission_request.py tests/api/test_change_meeting_api.py` to verify backend validation.

**Checkpoint**: User Story 1 hoàn thành - Backend từ chối mọi yêu cầu đổi ca nếu user không có mặt ở ca cũ.

---

## Phase 3: User Story 2 - Cập nhật Giao diện Web Frontend & Zalo Mini App (Priority: P2)

**Goal**: Bắt buộc chọn ca hiện tại trên các form đổi ca, loại bỏ tùy chọn rỗng "Đăng ký mới".

- [x] T006 [P] [US2] Update `PermissionFormModal.tsx` in `frontend/src/features/rbac/components/permissions/PermissionFormModal.tsx`:
  - Mark `old_meeting_id` with `rules: [{ required: true, message: 'Vui lòng chọn buổi sinh hoạt hiện tại!' }]`.
  - Remove `allowClear` and placeholder/tooltip about "đăng ký mới".
- [x] T007 [P] [US2] Update `PermissionFormModal.tsx` in `zalo-mini-app/dut-manager/src/features/permission_request/PermissionFormModal.tsx`:
  - Require `formOldMeetingId` for `CHANGE_MEETING`.
  - Remove option "Chưa có buổi học nào (Đăng ký mới)".
  - Add client-side validation check before submit.

---

## Phase 4: Verification & Polish

**Purpose**: Đồng bộ OpenAPI schema, typecheck và kiểm tra hồi quy toàn diện.

- [x] T008 Re-export `frontend/openapi.json` from FastAPI and run `npm run generate:api` in `frontend/`.
- [x] T009 Run TypeScript typecheck `npx tsc -b` in `frontend/`.
- [x] T010 Run full backend test suite `uv run pytest` to ensure zero regressions across all modules.
