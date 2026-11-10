# Tasks: Trainee Evaluation List in Meeting Detail

**Input**: Design documents from `/specs/057-trainee-evaluation-list/`  
**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`  
**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)

---

## Phase 1: Setup & Foundational Prerequisites

**Purpose**: Chuẩn bị component modal dùng chung và các type definitions nếu cần.

- [x] T001 [P] Create `EvaluationDetailModal.tsx` in `frontend/src/features/meeting/components/EvaluationDetailModal.tsx` to display full evaluation breakdown (criteria list, average score, feedback text, reviewer/target user info, and anonymity tags).
- [x] T002 Export `EvaluationDetailModal` in `frontend/src/features/meeting/components/index.ts`.

---

## Phase 2: User Story 1 - Xem danh sách và chi tiết đánh giá của từng Trainee (Priority: P1) 🎯 MVP

**Goal**: Cho phép Trainer/Admin thấy được trạng thái đánh giá của từng Trainee trong bảng điểm danh (`TraineeListTable`) và click xem chi tiết bài đánh giá của học viên.

- [x] T003 [US1] Update `TraineeListTable.tsx` in `frontend/src/features/meeting/components/participants/TraineeListTable.tsx` to accept `onViewEvaluation?: (evaluation: EvaluationResponse) => void`, making the evaluation Tag / action button clickable when an evaluation exists.
- [x] T004 [P] [US1] Update `ParticipantMobileList.tsx` in `frontend/src/features/meeting/components/participants/ParticipantMobileList.tsx` to display interactive evaluation status tags on mobile view.
- [x] T005 [US1] Update `MeetingParticipantsTab.tsx` in `frontend/src/features/meeting/components/MeetingParticipantsTab.tsx` to manage `selectedEvaluation` state and render `EvaluationDetailModal` when clicked from table or mobile cards.

**Checkpoint**: User Story 1 hoàn thành - Trainer có thể xem trạng thái đánh giá và click vào xem toàn văn chi tiết bài đánh giá của từng học viên trực tiếp từ danh sách người tham gia.

---

## Phase 3: User Story 2 - Lọc danh sách Trainee theo trạng thái đánh giá (Priority: P2)

**Goal**: Cung cấp bộ lọc trực quan giữa "Tất cả", "Đã đánh giá", "Chưa đánh giá" kèm số lượng thống kê rõ ràng.

- [x] T006 [US2] Enhance `EvaluationProgressFilterBar.tsx` in `frontend/src/features/meeting/components/participants/EvaluationProgressFilterBar.tsx` with clear counts, tooltips, and responsive segment/radio filters for rated vs unrated trainees.
- [x] T007 [US2] Ensure filter logic in `MeetingParticipantsTab.tsx` correctly handles excused/unexcused absent trainees when filtering unrated status.

**Checkpoint**: User Story 2 hoàn thành - Trainer có thể lọc ngay danh sách học viên chưa đánh giá để nhắc nhở.

---

## Phase 4: User Story 3 - Xem chi tiết Trainee đánh giá trong Tab Báo cáo Đánh giá (Priority: P3)

**Goal**: Bổ sung bảng danh sách tất cả các Trainee đã đánh giá trực tiếp trong tab "Báo cáo Đánh giá" (`MeetingEvaluationSummaryView`).

- [x] T008 [US3] Create `TraineeEvaluationListCard.tsx` in `frontend/src/features/meeting/components/summary/TraineeEvaluationListCard.tsx` to render a structured table of trainee evaluations (Trainee name/avatar, Target Trainer, Average score, Submitted date, Action button to view details).
- [x] T009 [P] [US3] Export `TraineeEvaluationListCard` in `frontend/src/features/meeting/components/summary/index.ts`.
- [x] T010 [US3] Integrate `TraineeEvaluationListCard` into `MeetingEvaluationSummaryView.tsx` in `frontend/src/features/meeting/components/MeetingEvaluationSummaryView.tsx` and wire up `EvaluationDetailModal`.

**Checkpoint**: User Story 3 hoàn thành - Tab Báo cáo Đánh giá có bảng tổng hợp danh sách Trainee đã đánh giá chuyên biệt.

---

## Phase 5: Verification & Polish

**Purpose**: Đảm bảo typecheck, bundle build và tuân thủ các quy tắc trong Hiến pháp dự án.

- [x] T011 Run TypeScript type check via `npx tsc -b` in `frontend/` to ensure zero compilation errors.
- [x] T012 Run frontend production build via `npm run build` in `frontend/`.
- [x] T013 Verify responsive UI on mobile and desktop breakpoints.
