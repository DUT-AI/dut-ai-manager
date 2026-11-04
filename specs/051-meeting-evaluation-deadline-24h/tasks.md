---
description: "Task list for meeting evaluation deadline 24 hours feature implementation"
---

# Tasks: Điều Chỉnh Thời Hạn Đánh Giá Cuộc Họp Từ 72 Giờ Về 24 Giờ (Meeting Evaluation Deadline 24 Hours)

**Input**: Design documents from `/specs/051-meeting-evaluation-deadline-24h/`  
**Prerequisites**: [plan.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/051-meeting-evaluation-deadline-24h/plan.md), [spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/051-meeting-evaluation-deadline-24h/spec.md), [research.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/051-meeting-evaluation-deadline-24h/research.md), [data-model.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/051-meeting-evaluation-deadline-24h/data-model.md), [contracts/](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/051-meeting-evaluation-deadline-24h/contracts/)

## Format: `[ID] [P?] [Story] Description with file path`
- **[P]**: Có thể thực hiện song song (khác tệp, không phụ thuộc vào task chưa hoàn thành)
- **[Story]**: Gán nhãn User Story tương ứng (`[US1]`, `[US2]`)

---

## Phase 1: Foundational (Hằng Số Miền Nghiệp Vụ)

**Mục đích**: Cập nhật nguồn chân lý duy nhất (Single Source of Truth) cho thời hạn đánh giá cuộc họp trong Domain layer

- [X] T001 Cập nhật hằng số nghiệp vụ `MEETING_EVALUATION_DEADLINE_HOURS: int = 24` trong `backend/app/meeting/domain/constants.py` và kiểm tra xuất khẩu tại `backend/app/meeting/domain/__init__.py`

**Checkpoint**: Hằng số nghiệp vụ đã được định nghĩa là 24 giờ.

---

## Phase 2: User Story 1 - Tự Động Ghi Nhận Vi Phạm Khi Quá 24 Giờ Chưa Đánh Giá (Priority: P1) 🎯 MVP

**Mục tiêu**: Hệ thống tự động xác định các cuộc họp kết thúc quá 24 giờ mà thành viên tham gia hoặc người phụ trách chưa nộp đánh giá để ghi nhận vi phạm kèm lý do "trong vòng 24h".

**Independent Test**: Chạy unit test kiểm tra mốc `end_bound` là 24h và xác nhận vi phạm được tạo mang lý do chứa chuỗi `"trong vòng 24h"`.

### Tests cho User Story 1 ⚠️
- [X] T002 [P] [US1] Cập nhật test case kiểm tra ngưỡng thời gian `end_bound` 24 giờ (`test_check_evaluation_deadline_uses_24h_bound_and_9d_window`) trong `backend/tests/unit/test_meeting_evaluation.py`
- [X] T003 [P] [US1] Cập nhật test case `test_check_evaluation_deadline_creates_violations_for_missing_evaluations` trong `backend/tests/unit/test_meeting_evaluation.py` để xác nhận lý do vi phạm chứa chuỗi `"trong vòng 24h"`

### Implementation cho User Story 1
- [X] T004 [US1] Cập nhật văn bản lý do vi phạm của Trainee và Trainer thành `"trong vòng 24h"` trong use case `CheckEvaluationDeadlineJobUseCase` tại `backend/app/meeting/application/check_evaluation_deadline_job_use_case.py`

**Checkpoint**: Đã hoàn thành User Story 1 (MVP). Logic kiểm tra vi phạm quá hạn 24 giờ hoạt động chính xác.

---

## Phase 3: User Story 2 - Cập Nhật Thông Điệp Cảnh Báo & Scheduler Job Name (Priority: P2)

**Mục tiêu**: Đồng bộ hóa toàn bộ mô tả, log và tên tác vụ trong hệ thống lập lịch sang mốc 24 giờ để tránh gây hiểu nhầm cho người dùng và quản trị viên.

**Independent Test**: Kiểm tra mã nguồn `meeting_evaluation_checker_job.py` và `scheduler.py` xác nhận không còn chứa con số 72h.

### Implementation cho User Story 2
- [X] T005 [P] [US2] Cập nhật docstring và thông điệp log từ 72h sang 24h trong `backend/app/jobs/meeting_evaluation_checker_job.py`
- [X] T006 [P] [US2] Cập nhật tên tác vụ định kỳ thành `"Check 24h meeting evaluations deadline"` trong `backend/app/core/scheduler.py`

**Checkpoint**: Đã hoàn thành User Story 2. Mọi thông điệp và nhãn tác vụ hiển thị đồng nhất mốc 24 giờ.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Mục đích**: Hoàn thiện chất lượng mã nguồn, kiểm thử hồi quy và xác minh toàn diện

- [X] T007 Chạy toàn bộ bộ test suite cuộc họp bằng `pytest` (`backend/.venv/bin/pytest tests/unit/test_meeting_evaluation.py -v`) để đảm bảo không có lỗi hồi quy (zero regressions)
- [X] T008 [P] Kiểm tra cú pháp, format và typing toàn bộ các tệp backend vừa chỉnh sửa bằng `ruff check backend/` và `ruff format --check backend/`

---

## Dependencies & Execution Order

### Thứ tự thực hiện các Phase:
1. **Foundational (Phase 1)**: Cập nhật hằng số `constants.py` (T001) - bắt đầu ngay.
2. **User Story 1 (Phase 2)**: Cập nhật tests và use case (T002, T003, T004).
3. **User Story 2 (Phase 3)**: Cập nhật job runner và scheduler name (T005, T006).
4. **Polish (Phase 4)**: Chạy toàn bộ test và kiểm tra linting (T007, T008).

### Cơ hội thực hiện song song (Parallel Execution):
- `T002` và `T003` có thể làm song song trong `test_meeting_evaluation.py`.
- `T005` (`meeting_evaluation_checker_job.py`) và `T006` (`scheduler.py`) có thể làm song song.
- `T008` (Ruff) có thể chạy độc lập.

---

## Implementation Strategy

### MVP First (Chỉ User Story 1):
1. Hoàn thành `T001` (Domain constant = 24).
2. Hoàn thành `T002` + `T003` + `T004` (Use case + Unit test).
3. Chạy `pytest` xác nhận logic 24h hoạt động.
4. Bổ sung `T005` + `T006` (Job name & log) và chạy Polish.
