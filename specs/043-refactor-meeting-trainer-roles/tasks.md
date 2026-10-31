---
description: "Task list for Refactoring Meeting Trainer & Trainee Roles"
---

# Tasks: Tách Biệt Vai Trò Trainer & Trainee Trong Quản Lý Buổi Học

**Input**: Design documents from `specs/043-refactor-meeting-trainer-roles/`  
**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/meeting-api.md`, `quickstart.md`

## Organization: Format `[ID] [P?] [Story] Description`
- **[P]**: Có thể thực hiện song song (khác file, không xung đột dependency).
- **[Story]**: Gắn với User Story tương ứng (`US1`, `US2`, `US3`).
- File paths chính xác theo kiến trúc dự án.

---

## Phase 1: Setup & Foundational Prerequisites

**Purpose**: Nâng cấp Database Schema và Core Domain Entities phục vụ phân loại vai trò.

- [X] T001 Tạo Alembic migration `backend/alembic/versions/040_add_role_to_meeting_participants.py` thêm cột `role VARCHAR(50) NOT NULL DEFAULT 'TRAINEE'`, tạo index và backfill dữ liệu lịch sử: cập nhật `role = 'TRAINER'` nếu đã có `created_by`, hoặc INSERT thêm 1 dòng Trainer (`user_id = created_by`, `role = 'TRAINER'`) nếu meeting chưa có `created_by` trong participants.
- [X] T002 [P] Thêm `ParticipantRole` enum (`TRAINER`, `TRAINEE`) trong `backend/app/meeting/domain/value_objects.py`.
- [X] T003 [P] Cập nhật entity `MeetingParticipant` trong `backend/app/meeting/domain/participant.py` bổ sung trường `role: ParticipantRole = ParticipantRole.TRAINEE`.
- [X] T004 [P] Cập nhật ORM model `MeetingParticipantModel` trong `backend/app/meeting/infrastructure/model.py` thêm cột `role`.
- [X] T005 Cập nhật `Meeting` entity trong `backend/app/meeting/domain/meeting.py` bổ sung các domain helpers: `trainers`, `trainees`, `is_trainer(user_id)`, `is_trainee(user_id)` (hỗ trợ nhiều Trainer bình đẳng).

**Checkpoint**: Nền tảng dữ liệu và domain Aggregate Root hoàn tất.

---

## Phase 2: User Story 1 - Phân loại nhiều Trainer và Trainee trên Form Tạo/Sửa & Backend DTOs (Priority: P1) 🎯 MVP

**Goal**: Cho phép tạo và chỉnh sửa buổi học chỉ định nhiều Trainer và Trainee riêng biệt, cho phép buổi tự học nhóm không có Trainer. Tuyệt đối không dùng fallback qua `user_ids` hay `created_by`.

- [X] T006 [P] [US1] Cập nhật schemas `MeetingCreate`, `MeetingUpdate`, `MeetingResponse`, `ParticipantResponse` trong `backend/app/meeting/schemas/meeting_schemas.py` và `backend/app/meeting/schemas/participant_schemas.py` (chỉ dùng `trainer_ids` và `trainee_ids`, loại bỏ hoàn toàn `user_ids`).
- [X] T007 [US1] Cập nhật `CreateMeetingUseCase` trong `backend/app/meeting/application/create_meeting_use_case.py` lưu participants theo đúng `role`, khử trùng lặp (ưu tiên `TRAINER`), hỗ trợ `trainer_ids` rỗng cho tự học nhóm.
- [X] T008 [US1] Cập nhật `UpdateMeetingUseCase` trong `backend/app/meeting/application/update_meeting_use_case.py` đồng bộ danh sách trainers và trainees theo role.
- [X] T009 [P] [US1] Cập nhật frontend types trong `frontend/src/features/meeting/types/meeting.types.ts` (`ParticipantRole`, `trainer_ids`, `trainee_ids`, `trainers`).
- [X] T010 [US1] Cập nhật `MeetingModal.tsx` trong `frontend/src/features/meeting/components/MeetingModal.tsx` phân tách 2 ô chọn rõ ràng: Trainer(s) phụ trách và Trainee(s) tham gia (hỗ trợ chọn theo Team).
- [X] T011 [P] [US1] Viết unit tests cho `CreateMeetingUseCase` và `UpdateMeetingUseCase` trong `backend/tests/unit/test_meeting_use_cases.py`.

**Checkpoint**: User Story 1 hoàn thành độc lập, form tạo/sửa lưu chuẩn xác role trong DB.

---

## Phase 3: User Story 2 - Trao toàn quyền điều hành Meeting cho tất cả Trainer (Priority: P2)

**Goal**: Mọi Trainer được phân công (dù không phải creator) đều có toàn quyền quản lý, điểm danh và nộp đánh giá tổng thể buổi học.

**Independent Test**: Đăng nhập với tài khoản của Trainer (khác `created_by`), thực hiện điểm danh học viên và nộp đánh giá tổng thể thành công (không bị lỗi 403).

- [X] T012 [US2] Cập nhật `check_meeting_ownership` và `check_meeting_evaluation_permission` trong `backend/app/meeting/controllers/dependencies.py` cấp quyền cho `meeting.is_trainer(current_user.id)`.
- [X] T013 [US2] Cập nhật `SubmitMeetingOverallEvaluationUseCase` trong `backend/app/meeting/application/submit_meeting_overall_evaluation_use_case.py` cho phép bất kỳ Trainer nào của meeting nộp đánh giá.
- [X] T014 [P] [US2] Cập nhật `UpdateParticipantStatusUseCase` trong `backend/app/meeting/application/update_participant_status_use_case.py` cho phép Trainer cập nhật trạng thái điểm danh học viên.
- [X] T015 [P] [US2] Viết API test kiểm tra quyền điều hành của Trainer trong `backend/tests/api/test_meeting_api.py`.

**Checkpoint**: User Story 2 hoàn thành, phân quyền điều hành lớp học thuộc về các Trainer thực tế.

---

## Phase 4: User Story 3 - Tách biệt 2 Bảng UI & Đồng bộ luồng Đánh giá / Nhắc nhở (Priority: P3)

**Goal**: Tách biệt rõ ràng 2 bảng Giảng viên và Học viên trên UI, hỗ trợ học viên chọn Trainer khi đánh giá và đồng bộ scanner nhắc việc.

**Independent Test**: Mở giao diện chi tiết buổi học, quan sát thấy 2 bảng riêng biệt. Khi bấm đánh giá, học viên có thể chọn Trainer cần gửi đánh giá.

- [X] T016 [P] [US3] Tạo component `TrainerListTable.tsx` trong `frontend/src/features/meeting/components/participants/TrainerListTable.tsx` (bảng riêng cho Trainer, hiển thị trạng thái điểm danh, ảnh quẹt thẻ, điểm đánh giá TB, không có nút chấm điểm học viên).
- [X] T017 [P] [US3] Tạo component `TraineeListTable.tsx` trong `frontend/src/features/meeting/components/participants/TraineeListTable.tsx` (bảng riêng cho Trainee, có đầy đủ cột đổi trạng thái điểm danh và nút chấm điểm học viên).
- [X] T018 [US3] Cập nhật `MeetingParticipantsTab.tsx` trong `frontend/src/features/meeting/components/MeetingParticipantsTab.tsx` tích hợp 2 bảng riêng biệt (`TrainerListTable` và `TraineeListTable`), gắn thanh lọc tiến độ với bảng Trainee.
- [X] T019 [P] [US3] Cập nhật `ParticipantListModal.tsx` trong `frontend/src/features/meeting/components/ParticipantListModal.tsx` phân tách thành 2 bảng/section Giảng viên và Học viên.
- [X] T020 [P] [US3] Cập nhật `ParticipantMobileList.tsx` trong `frontend/src/features/meeting/components/participants/ParticipantMobileList.tsx` hiển thị tách biệt 2 nhóm Trainer và Trainee.
- [X] T021 [US3] Cập nhật `TraineeEvaluationModal.tsx` trong `frontend/src/features/meeting/components/TraineeEvaluationModal.tsx` cho phép chọn Trainer cụ thể khi meeting có nhiều Trainer phụ trách.
- [X] T022 [US3] Cập nhật `SubmitTraineeEvaluationUseCase` trong `backend/app/meeting/application/submit_trainee_evaluation_use_case.py` xác thực `target_user_id` thuộc danh sách Trainer của buổi học.
- [X] T023 [US3] Cập nhật `MeetingEvaluationTaskScanner` trong `backend/app/reminder/application/scanners/meeting_evaluation_scanner.py` và `CheckEvaluationDeadlineJobUseCase` trong `backend/app/meeting/application/check_evaluation_deadline_job_use_case.py` quét danh sách `meeting.trainers` thay vì `meeting.created_by`.

**Checkpoint**: User Story 3 hoàn thành, UI hiển thị 2 bảng riêng biệt, luồng đánh giá và scanner hoạt động chính xác.

---

## Phase 5: Polish & Regression Testing

**Purpose**: Đảm bảo toàn bộ hệ thống hoạt động ổn định và không phát sinh lỗi hồi quy.

- [X] T024 [P] Chạy backend test suite `cd backend && uv run pytest tests/` đảm bảo 100% tests pass.
- [X] T025 [P] Chạy frontend build `cd frontend && npm run build` đảm bảo không có lỗi type và compile.
- [X] T026 Thực hiện kiểm thử toàn diện theo kịch bản trong `quickstart.md`.

---

## Dependencies & Execution Order

- **Phase 1 (Setup)** -> Phải hoàn thành trước tiên (T001 - T005).
- **Phase 2 (US1)** -> Triển khai DTOs backend và Form frontend (T006 - T011).
- **Phase 3 (US2)** -> Triển khai phân quyền và quyền nộp đánh giá cho Trainer (T012 - T015).
- **Phase 4 (US3)** -> Triển khai 2 bảng UI riêng biệt, modal chọn trainer và scanner (T016 - T023).
- **Phase 5 (Polish)** -> Kiểm thử toàn diện và nghiệm thu (T024 - T026).
