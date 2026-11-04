# Tasks: Tinh giản Đánh giá Meeting & Chuẩn hóa Kiến trúc Full Stack

**Input**: Design documents from `/specs/046-harden-meeting-evaluation/` (`spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`)  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`  
**Constitution**: Enforce Principle XIV (No Fake Optionals), Principle X (Zero Redundant Compatibility), Principle VIII (Frontend Modularity), and Principle I (DDD Boundaries).  

## Format: `[TaskID] [P?] [Story?] Description with file path`

- **[P]**: Can run in parallel (different files, no blocking dependencies)
- **[Story]**: Which user story this task belongs to (`[US1]`, `[US2]`, `[US3]`)
- Include exact file paths in every task description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Xác minh môi trường và kiểm tra trạng thái baseline trước khi sửa đổi.

- [X] T001 Verify baseline tests pass with zero regressions in `backend` via `poetry run pytest tests/unit/test_meeting_evaluation.py tests/api/test_meeting_api.py` and `frontend` via `npx tsc --noEmit`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Chuẩn hóa nền tảng Domain và Contracts trước khi thực hiện các User Stories.

**⚠️ CRITICAL**: Các task này phải hoàn tất trước khi triển khai các User Story.

- [X] T002 [P] Verify 0 dead code and proper accented Vietnamese strings in `backend/app/meeting/domain/participant.py`
- [X] T003 [P] Document deprecation of `POST /meetings/{meeting_id}/evaluations/trainer` in API contract `specs/046-harden-meeting-evaluation/contracts/meeting-evaluation-api.yaml`

**Checkpoint**: Nền tảng domain và contract đã sẵn sàng - có thể tiến hành song song các user story.

---

## Phase 3: User Story 1 - Tinh giản Trách nhiệm Đánh giá của Giảng viên (Priority: P1) 🎯 MVP

**Goal**: Giảng viên chỉ gửi 1 phiếu đánh giá tổng thể duy nhất cho toàn bộ buổi học (`MeetingOverallEvaluation`). Bỏ hoàn toàn luồng Trainer chấm điểm từng Trainee lẻ tẻ (`TRAINER_TO_TRAINEE`). Trainee tiếp tục đánh giá Trainer phụ trách (`TRAINEE_TO_TRAINER`).

**Independent Test**:
- Đăng nhập tài khoản Trainer, vào trang chi tiết buổi học.
- Bảng danh sách học viên (`TraineeListTable`) không còn cột hay nút "Chấm điểm" từng học viên.
- Trainer gửi Đánh giá tổng thể thành công qua modal trên Header.
- Gọi API `POST /{meeting_id}/evaluations/trainer` trả về `400 Bad Request` hướng dẫn dùng đánh giá tổng thể.

### Implementation for User Story 1

- [X] T004 [P] [US1] Disable individual trainer-to-trainee evaluation endpoint `POST /{meeting_id}/evaluations/trainer` with 400 Bad Request in `backend/app/meeting/controllers/evaluation_controller.py`
- [X] T005 [P] [US1] Refactor `GetMyEvaluationResultUseCase` in `backend/app/meeting/application/get_my_evaluation_result_use_case.py` to eliminate hardcoded assumptions on `meeting.created_by` and return safely
- [X] T006 [P] [US1] Delete obsolete modal `frontend/src/features/meeting/components/TrainerEvaluationModal.tsx` and remove its export from `frontend/src/features/meeting/components/index.ts`
- [X] T007 [US1] Remove individual evaluation buttons ("Chấm điểm" / "Đã ĐG") and `onEvaluate` / `existingEvaluation` props from `frontend/src/features/meeting/components/ParticipantActionButtons.tsx`
- [X] T008 [US1] Remove Trainer-to-Trainee rating column, filter, and `onEvaluate` callback from `frontend/src/features/meeting/components/participants/TraineeListTable.tsx`
- [X] T009 [US1] Remove `onEvaluate` and evaluation actions from `frontend/src/features/meeting/components/participants/ParticipantListTable.tsx` and `frontend/src/features/meeting/components/participants/ParticipantMobileList.tsx`
- [X] T010 [US1] Clean up `MeetingParticipantsTab.tsx` in `frontend/src/features/meeting/components/MeetingParticipantsTab.tsx` by removing `TrainerEvaluationModal`, `trainerEvalsByTraineeId` mapping, and rating state
- [X] T011 [P] [US1] Update `frontend/src/features/meeting/components/participants/TraineeEvaluationCard.tsx` and `frontend/src/features/meeting/components/participants/EvaluationProgressFilterBar.tsx` to focus exclusively on Trainee-to-Trainer evaluation progress
- [X] T012 [US1] Update unit tests in `backend/tests/unit/test_meeting_evaluation.py` to reflect discontinuation of individual trainer evaluation

**Checkpoint**: User Story 1 hoàn tất - Giao diện sạch sẽ, Trainer chỉ gửi 1 đánh giá tổng thể cho cả lớp.

---

## Phase 4: User Story 2 - Siết chặt Invariants & Chống Tự Đánh giá (Priority: P2)

**Goal**: Chặn tuyệt đối hành vi tự đánh giá bản thân (`reviewer_id == target_user_id`), bắt buộc `target_user_id` phải là Trainer của buổi học, và kiểm tra quyền Trainer/Admin gửi đánh giá tổng thể.

**Independent Test**:
- Trainee gửi đánh giá Trainer với `reviewer_id == target_user_id`: Hệ thống từ chối với lỗi `400 Bad Request: "Không thể tự đánh giá chính mình"`.
- Gửi đánh giá Trainer với `target_user_id` không phải Trainer của buổi học: Hệ thống từ chối với lỗi `400 Bad Request: "Người được đánh giá không phải là Trainer của buổi học này"`.
- Gửi đánh giá tổng thể từ tài khoản không phải Trainer/Admin: Hệ thống từ chối với lỗi `403 Forbidden`.

### Implementation for User Story 2

- [X] T013 [P] [US2] Enforce invariant checks against self-evaluation (`reviewer_id == resolved_target_id`) and invalid trainer role in `backend/app/meeting/application/submit_trainee_evaluation_use_case.py`
- [X] T014 [P] [US2] Enforce role invariant verification (trainer, creator, or admin) in `backend/app/meeting/application/submit_meeting_overall_evaluation_use_case.py`
- [X] T015 [US2] Add automated unit tests for self-evaluation prevention, trainer validation, and overall evaluation authorization in `backend/tests/unit/test_meeting_evaluation.py`

**Checkpoint**: User Story 2 hoàn tất - Toàn bộ Domain Invariants được bảo vệ nghiêm ngặt.

---

## Phase 5: User Story 3 - Tuân thủ Hiến pháp & Trải nghiệm Người dùng (Priority: P3)

**Goal**: Tuân thủ Điều XIV của Hiến pháp (No Fake Optionals) trong `GetMeetingEvaluationSummaryUseCase`; loại bỏ truy vấn SQL lặp giữa Permission Dependency và Use Case; hiển thị mốc thời gian hạn chót đánh giá trên `MeetingHeroHeader`.

**Independent Test**:
- Khởi tạo `GetMeetingEvaluationSummaryUseCase` bắt buộc phải có 3 repos (không còn `| None = None`).
- Request `POST /{meeting_id}/evaluations/overall` chỉ thực hiện đúng 1 truy vấn `meeting` trong log DB.
- Xem giao diện `MeetingHeroHeader` thấy Tag hiển thị rõ ràng hạn chót đánh giá (`Hạn chót: DD/MM/YYYY HH:mm` hoặc `Đã hết hạn`).

### Implementation for User Story 3

- [X] T016 [P] [US3] Enforce Constitution Principle XIV by making `overall_eval_repo: MeetingOverallEvaluationRepository` non-nullable and removing `if self.overall_eval_repo:` in `backend/app/meeting/application/get_meeting_evaluation_summary_use_case.py`
- [X] T017 [P] [US3] Eliminate duplicate database query by removing redundant `check_meeting_evaluation_permission` dependency and passing `is_admin` to use case in `backend/app/meeting/controllers/evaluation_controller.py`
- [X] T018 [US3] Update constructor calls and test fixtures for `GetMeetingEvaluationSummaryUseCase` in `backend/tests/unit/test_meeting_evaluation.py`
- [X] T019 [P] [US3] Display formatted `evaluation_deadline` badge with active/expired status on `frontend/src/features/meeting/components/MeetingHeroHeader.tsx`

**Checkpoint**: User Story 3 hoàn tất - Mã nguồn tuân thủ Hiến pháp, giảm 50% truy vấn DB và UX hiển thị hạn chót minh bạch.

---

## Phase 6: Polish & Cross-Cutting Concerns (Initial Rollout)

**Purpose**: Kiểm thử tích hợp toàn diện và kiểm tra chất lượng mã nguồn đợt 1.

- [X] T020 [P] Run full backend test suite to guarantee 100% pass via `cd backend && poetry run pytest tests/unit/test_meeting_evaluation.py tests/api/test_meeting_api.py`
- [X] T021 [P] Run frontend TypeScript type checking and production build via `cd frontend && npx tsc --noEmit && npm run build`
- [X] T022 Validate end-to-end scenarios per validation guide in `specs/046-harden-meeting-evaluation/quickstart.md`

---

## Phase 7: User Story 4 - Loại bỏ Dead Code, Component Mồ côi & Tinh giản Báo cáo Đánh giá (Priority: P4)

**Goal**: Dọn sạch dứt điểm toàn bộ dead code, file mồ côi không dùng đến, modal xem điểm cá nhân cũ, và khối báo cáo Trainer chấm lẻ học viên ở cả Frontend và Backend để mã nguồn tinh gọn, đạt chuẩn Clean Architecture và giao diện không gây hiểu nhầm.

**Independent Test**:
- Kiểm tra mã nguồn Frontend: Không còn các file `ParticipantListModal.tsx`, `ParticipantListTable.tsx`, `MeetingTraineeEvaluationBanner.tsx`, `MyEvaluationResultModal.tsx`.
- Giao diện Header & Banner: Không còn nút "Điểm của tôi" / "Xem Điểm của tôi".
- Tab Báo cáo Đánh giá: Ẩn cột/card "Trainer đánh giá Trainee" khi không có dữ liệu (`trainerCount === 0`).
- Kiểm tra Backend: Đã xóa `SubmitTrainerEvaluationUseCase.py`, không còn import thừa hay DTO rác.
- Backend test (`pytest`) và Frontend check (`npx tsc --noEmit` & `npm run build`) đạt 100% pass.

### Implementation for User Story 4

- [X] T023 [P] [US4] Delete orphan components `frontend/src/features/meeting/components/ParticipantListModal.tsx`, `frontend/src/features/meeting/components/participants/ParticipantListTable.tsx`, and `frontend/src/features/meeting/components/MeetingTraineeEvaluationBanner.tsx`, and remove their exports from `components/index.ts` and `components/participants/index.ts`
- [X] T024 [P] [US4] Delete obsolete modal `frontend/src/features/meeting/components/MyEvaluationResultModal.tsx` and remove its export from `frontend/src/features/meeting/components/index.ts`
- [X] T025 [P] [US4] Remove "Điểm của tôi" button and `onOpenMyResult` prop from `frontend/src/features/meeting/components/MeetingHeroHeader.tsx`
- [X] T026 [P] [US4] Remove "Xem Điểm của tôi" button and `onOpenMyResult` prop from `frontend/src/features/meeting/components/participants/TraineeEvaluationCard.tsx`
- [X] T027 [US4] Remove `onOpenMyResult` prop plumbing from `frontend/src/features/meeting/components/MeetingParticipantsTab.tsx` and `frontend/src/features/meeting/pages/MeetingDetailPage.tsx` (remove `isMyResultOpen` state and `MyEvaluationResultModal` mount)
- [X] T028 [P] [US4] Clean up obsolete hooks, services, and types in `frontend/src/features/meeting/hooks/useMeetings.ts` (remove `useMyEvaluationResult`), `services/meeting.service.ts` (remove `submitTrainerEvaluation` and `getMyEvaluationResult`), `hooks/useMeetingPermissions.ts` (remove `canEvaluateTrainee`), and `types/meeting.types.ts` (remove `TrainerSubmitEvaluationPayload`)
- [X] T029 [P] [US4] Remove unused `isEnded` prop from `frontend/src/features/meeting/components/ParticipantActionButtons.tsx`
- [X] T030 [P] [US4] Delete backend dead code `backend/app/meeting/application/submit_trainer_evaluation_use_case.py` and unregister it from `backend/app/meeting/providers.py` and `backend/app/meeting/application/__init__.py`
- [X] T031 [P] [US4] Clean up unused imports (`Annotated`, `Depends`, `SubmitTrainerEvaluationUseCase`) in `backend/app/meeting/controllers/evaluation_controller.py` and remove unused schema in `backend/app/meeting/schemas/evaluation_schemas.py`
- [X] T032 [US4] Update backend unit tests in `backend/tests/unit/test_meeting_evaluation.py` to remove references to deleted `SubmitTrainerEvaluationUseCase`
- [X] T033 [P] [US4] Refactor `frontend/src/features/meeting/components/MeetingEvaluationSummaryView.tsx`, `EvaluationOverviewCards.tsx`, and `EvaluationCriteriaBreakdownCards.tsx` to conditionally hide the "Trainer đánh giá Trainee" card and criteria list when `trainerCount === 0`, ensuring clean reporting for new meetings

---

## Phase 8: Final Polish & Verification

**Purpose**: Xác minh toàn diện chất lượng mã nguồn sau khi tổng vệ sinh.

- [X] T034 [P] Run full backend test suite to guarantee 100% pass via `cd backend && poetry run pytest tests/unit/test_meeting_evaluation.py tests/api/test_meeting_api.py`
- [X] T035 [P] Run frontend TypeScript type checking and production build via `cd frontend && npx tsc --noEmit && npm run build`
- [X] T036 Run flake8 on backend meeting module via `cd backend && poetry run flake8 app/meeting/ --select=F401,F841`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Không có dependencies - Đã hoàn tất.
- **Foundational (Phase 2)**: Đã hoàn tất.
- **User Stories (Phase 3 - 5)**: Đã hoàn tất (US1, US2, US3).
- **Polish Đợt 1 (Phase 6)**: Đã hoàn tất.
- **User Story 4 (Phase 7)**: Có thể thực hiện ngay lập tức sau khi xác định danh sách dead code.
- **Final Polish (Phase 8)**: Chạy sau khi hoàn tất User Story 4.

### Within User Story 4

- Xóa các file mồ côi (T023, T024, T030) có thể chạy song song.
- Dọn dẹp buttons & props trên FE (T025, T026, T027, T028, T029) có thể làm song song hoặc theo luồng Component -> Page.
- Tinh giản giao diện Báo cáo Đánh giá (T033) độc lập với dọn dẹp backend (T031, T032).
- Verification (T034, T035, T036) chạy sau cùng để chốt chất lượng xanh.

### Parallel Opportunities in User Story 4

```bash
# Frontend Deletions & Cleanups in parallel:
Task: "T023 [P] [US4] Delete orphan components ParticipantListModal, ParticipantListTable, MeetingTraineeEvaluationBanner"
Task: "T024 [P] [US4] Delete obsolete modal MyEvaluationResultModal"
Task: "T025 [P] [US4] Remove Điểm của tôi button on MeetingHeroHeader"
Task: "T026 [P] [US4] Remove Xem Điểm của tôi button on TraineeEvaluationCard"
Task: "T028 [P] [US4] Clean up obsolete hooks, services, and types"
Task: "T029 [P] [US4] Remove unused isEnded prop in ParticipantActionButtons"
Task: "T033 [P] [US4] Refactor MeetingEvaluationSummaryView to hide empty Trainer-to-Trainee blocks"

# Backend Cleanups in parallel:
Task: "T030 [P] [US4] Delete backend dead code submit_trainer_evaluation_use_case.py"
Task: "T031 [P] [US4] Clean up unused imports in evaluation_controller.py"
```

---

## Implementation Strategy

### Incremental Delivery & Safe Cleanup
1. **Bước 1**: Xóa bỏ các file mồ côi hoàn toàn không có ai dùng (`ParticipantListModal`, `ParticipantListTable`, `MeetingTraineeEvaluationBanner`).
2. **Bước 2**: Dọn dẹp nút "Điểm của tôi" / modal `MyEvaluationResultModal` và các props liên quan trên Frontend.
3. **Bước 3**: Dọn dẹp dead code Backend (`SubmitTrainerEvaluationUseCase`, unregister DI, dọn import thừa).
4. **Bước 4**: Tinh giản Tab Báo cáo Đánh giá để ẩn các khối Trainer chấm lẻ khi không có dữ liệu.
5. **Bước 5**: Chạy `flake8`, `pytest`, `tsc` và `npm run build` để đảm bảo 0 regression.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Không có dependencies - Chạy ngay để xác nhận trạng thái xanh ban đầu.
- **Foundational (Phase 2)**: Phụ thuộc vào Phase 1 - Chuẩn hóa domain và API contract trước khi sửa logic.
- **User Stories (Phase 3+)**:
  - **User Story 1 (P1 - MVP)**: Có thể bắt đầu ngay sau Phase 2.
  - **User Story 2 (P2)**: Có thể bắt đầu song song hoặc sau US1.
  - **User Story 3 (P3)**: Có thể bắt đầu song song hoặc sau US1/US2.
- **Polish (Phase 6)**: Chạy sau khi hoàn tất cả 3 User Stories.

### Within Each User Story

- Backend Use Case / Controller modifications hoàn thành cùng lúc với Frontend components.
- Cập nhật Unit Tests để kiểm tra tính đúng đắn ngay sau khi thay đổi logic.

### Parallel Opportunities

- **Phase 3 (US1)**:
  - T004 (backend controller), T005 (backend use case), T006 (FE modal deletion), T011 (FE card/progress) có thể làm song song.
- **Phase 4 (US2)**:
  - T013 (`submit_trainee_evaluation_use_case.py`) và T014 (`submit_meeting_overall_evaluation_use_case.py`) có thể làm song song vì là 2 file độc lập.
- **Phase 5 (US3)**:
  - T016 (Backend use case Fake Optional), T017 (Backend controller query optimization), T019 (Frontend HeroHeader deadline) có thể làm song song.
- **Phase 6 (Polish)**:
  - T020 (Pytest backend) và T021 (Frontend tsc/build) có thể chạy song song.

---

## Parallel Example: User Story 1

```bash
# Backend Tasks in parallel:
Task: "T004 [P] [US1] Disable individual trainer-to-trainee evaluation endpoint in backend/app/meeting/controllers/evaluation_controller.py"
Task: "T005 [P] [US1] Refactor GetMyEvaluationResultUseCase in backend/app/meeting/application/get_my_evaluation_result_use_case.py"

# Frontend Tasks in parallel:
Task: "T006 [P] [US1] Delete obsolete modal frontend/src/features/meeting/components/TrainerEvaluationModal.tsx"
Task: "T011 [P] [US1] Update TraineeEvaluationCard and Progress bar in frontend/src/features/meeting/components/participants/"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Hoàn tất Phase 1 (Setup) và Phase 2 (Foundational).
2. Hoàn tất Phase 3 (User Story 1 - Tinh giản Trách nhiệm Trainer).
3. **VALIDATE MVP**: Kiểm tra bảng học viên không còn nút chấm điểm cá nhân, Trainer chỉ chấm tổng thể 1 lần cho cả lớp.

### Incremental Delivery
1. **Giao đoạn 1**: Hoàn tất User Story 1 -> Giải quyết triệt để vấn đề UX và áp lực chấm điểm học viên.
2. **Giai đoạn 2**: Hoàn tất User Story 2 -> Siết chặt Domain Invariants, chống tự đánh giá bản thân.
3. **Giai đoạn 3**: Hoàn tất User Story 3 -> Đạt chuẩn Hiến pháp Điều XIV (No Fake Optionals), tối ưu 50% truy vấn DB, hiển thị hạn chót rõ ràng.
4. **Giai đoạn 4**: Chạy toàn bộ test suites và kiểm thử hoàn chỉnh theo `quickstart.md`.
