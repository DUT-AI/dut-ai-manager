# Phase 1: Background Job & Use Case Contracts (038-violation-delay)

Tài liệu này đặc tả giao diện (signatures), tham số đầu vào và hành vi kỳ vọng của các use case và job nền phục vụ kiểm tra vi phạm.

---

## 1. Domain Constants Contracts

### `app.violation.domain.constants`
```python
DEFAULT_VIOLATION_CHECK_DELAY_DAYS: int = 2
```

### `app.homework.domain.constants`
```python
HOMEWORK_VIOLATION_CHECK_DELAY_DAYS: int = 2
```

### `app.meeting.domain.constants`
```python
MEETING_ATTENDANCE_CHECK_DELAY_DAYS: int = 2
MEETING_EVALUATION_DEADLINE_HOURS: int = 72
MEETING_EVALUATION_SCAN_WINDOW_DAYS: int = 9
```

### `app.duty.domain.constants`
```python
DUTY_VIOLATION_CHECK_DELAY_DAYS: int = 2
```

---

## 2. Use Case Signatures & Behavior

### `CheckOverdueHomeworkUseCase`
- **File**: `backend/app/homework/application/check_overdue_homework_use_case.py`
- **Constructor Dependencies**:
  - `homework_repo: HomeworkRepository`
  - `homework_submission_repo: HomeworkSubmissionRepository`
  - `homework_assignee_repo: HomeworkAssigneeRepository`
  - `event_bus: type[EventBus] = EventBus`
  *(Đã loại bỏ hoàn toàn QuizApiClient & UserRepo, đối soát trực tiếp giữa Assignee và Submission trong DB để đảm bảo độ tin cậy và hiệu năng cao).*
- **Signature**:
  ```python
  async def execute(self, target_date: date | None = None) -> int
  ```
- **Contract Rules**:
  - Khi `target_date is None`:
    ```python
    now_vn = datetime.now(UTC).astimezone(ZoneInfo("Asia/Ho_Chi_Minh"))
    target_date = now_vn.date() - timedelta(days=HOMEWORK_VIOLATION_CHECK_DELAY_DAYS)
    ```
  - Khi `target_date is not None`:
    Sử dụng chính xác giá trị `target_date` được truyền vào (không trừ thêm ngày).
  - Trả về số lượng sự kiện `HomeworkOverdueDetected` đã phát tán.

---

### `CheckMeetingAttendanceUseCase`
- **File**: `backend/app/meeting/application/check_meeting_attendance_use_case.py`
- **Signature**:
  ```python
  async def execute(self, target_date: date | None = None) -> int
  ```
- **Contract Rules**:
  - Khi `target_date is None`:
    ```python
    now_vn = datetime.now(UTC).astimezone(ZoneInfo("Asia/Ho_Chi_Minh"))
    target_date = now_vn.date() - timedelta(days=MEETING_ATTENDANCE_CHECK_DELAY_DAYS)
    ```
  - Khi `target_date is not None`:
    Sử dụng chính xác giá trị `target_date` được truyền vào.
  - Trả về số lượng sự kiện điểm danh vi phạm đã phát tán.

---

### `CheckOverdueDutiesUseCase`
- **File**: `backend/app/duty/application/check_overdue_duties_use_case.py`
- **Signature**:
  ```python
  async def execute(self, target_date: date | None = None) -> int
  ```
- **Contract Rules**:
  - Khi `target_date is None`:
    ```python
    now_vn = datetime.now(UTC).astimezone(ZoneInfo("Asia/Ho_Chi_Minh"))
    target_date = now_vn.date() - timedelta(days=DUTY_VIOLATION_CHECK_DELAY_DAYS)
    ```
  - Khi `target_date is not None`:
    Sử dụng chính xác giá trị `target_date` được truyền vào.
  - Trả về số lượng vi phạm trực nhật đã tạo.

---

### `CheckEvaluationDeadlineJobUseCase`
- **File**: `backend/app/meeting/application/check_evaluation_deadline_job_use_case.py`
- **Signature**:
  ```python
  async def execute(self) -> dict
  ```
- **Contract Rules**:
  - Quét trong khoảng:
    ```python
    now = datetime.now(UTC)
    start_bound = now - timedelta(days=MEETING_EVALUATION_SCAN_WINDOW_DAYS)
    end_bound = now - timedelta(hours=MEETING_EVALUATION_DEADLINE_HOURS)
    ```
  - Lý do vi phạm tra cứu và ghi nhận:
    - Trainee: `"Chưa hoàn thành đánh giá Trainer cho buổi học '{meeting.title}'{time_str} trong vòng 72h"`
    - Trainer: `"Trainer chưa hoàn tất đánh giá tổng thể buổi học '{meeting.title}'{time_str} trong vòng 72h"`
  - Trả về dictionary thống kê: `{"meetings_scanned": int, "trainee_violations_created": int, "trainer_violations_created": int}`.
