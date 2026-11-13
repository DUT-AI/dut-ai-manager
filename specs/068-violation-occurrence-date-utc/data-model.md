# Data Model: Chuẩn Hóa Thời Gian Xảy Ra Vi Phạm Tự Động Theo UTC

## Entities & Events

### 1. Entity: `Violation` (Domain Entity)
- **Path**: `backend/app/violation/domain/entity.py`
- **Fields**:
  - `id: int | None`
  - `user_id: int`
  - `reason: str`
  - `date: datetime` (*Timezone-Aware UTC* đại diện cho thời điểm vi phạm xảy ra)
  - `created_at: datetime` (*Timezone-Aware UTC*, thời điểm bản ghi được tạo)
  - `updated_at: datetime` (*Timezone-Aware UTC*, thời điểm bản ghi được cập nhật)
  - `created_by: int | None`
  - `updated_by: int | None`
  - `is_deleted: bool`
  - `owner: UserRef | None`
  - `creator: UserRef | None`
  - `updater: UserRef | None`

**Quy tắc nghiệp vụ**:
- Trường `date` PHẢI là timezone-aware UTC (`tzinfo=UTC`).
- Trường `date` KHÔNG ĐƯỢC gán theo thời gian chạy scheduler (`datetime.now(UTC)`), trừ trường hợp đặc biệt không thể truy vết được mốc thời gian sự kiện.

---

### 2. Domain Events Update

#### A. `ParticipantAbsenceRecorded`
- **Path**: `backend/app/meeting/domain/events.py`
- **Attributes**:
  ```python
  class ParticipantAbsenceRecorded(DomainEvent):
      user_id: int
      meeting_id: int
      meeting_title: str
      meeting_date: str
      start_time: datetime | None = None  # Timestamp bắt đầu buổi họp (UTC aware)
  ```

#### B. `ParticipantLateRecorded`
- **Path**: `backend/app/meeting/domain/events.py`
- **Attributes**:
  ```python
  class ParticipantLateRecorded(DomainEvent):
      user_id: int
      meeting_id: int
      meeting_title: str
      check_in_at: datetime  # Thời điểm check-in thực tế của học viên (UTC aware)
      start_time: datetime   # Thời điểm bắt đầu buổi họp (UTC aware)
  ```

#### C. `HomeworkOverdueDetected`
- **Path**: `backend/app/homework/domain/value_objects.py`
- **Attributes**:
  ```python
  class HomeworkOverdueDetected(DomainEvent):
      user_id: int
      homework_id: int
      homework_title: str
      deadline_date: str
      reason: str = "Không nộp bài tập"
      uncompleted_items: list[str] = []
      deadline: datetime | None = None  # Deadline chính xác của học viên (UTC aware)
  ```

---

## Mapping Logic per Violation Type

| Loại vi phạm | Job / Handler | Thời điểm xảy ra (`date`) | Fallback nếu thiếu |
|---|---|---|---|
| **Vắng sinh hoạt** | `AutomatedViolationHandler._handle_meeting_absence` | `ensure_utc(event.start_time)` | `datetime.now(UTC)` |
| **Đi trễ sinh hoạt** | `AutomatedViolationHandler._handle_meeting_late` | `ensure_utc(event.check_in_at)` | `datetime.now(UTC)` |
| **Quá hạn bài tập** | `AutomatedViolationHandler._handle_homework_overdue` | `ensure_utc(event.deadline)` | `datetime.now(UTC)` |
| **Trực nhật có họp** | `CheckOverdueDutiesUseCase.execute` | `ensure_utc(meeting.end_time)` | `datetime.now(UTC)` |
| **Trực nhật tự do** | `CheckOverdueDutiesUseCase.execute` | `ensure_utc(datetime.combine(duty.duty_date, time(23, 59, 59)))` | `datetime.now(UTC)` |
| **Quá hạn đánh giá 24h** | `CheckEvaluationDeadlineJobUseCase.execute` | `ensure_utc(meeting.end_time) + timedelta(hours=24)` | `datetime.now(UTC)` |
| **Xin phép vượt giới hạn** | `PermissionViolationHandler.handle` | `ensure_utc(event.start_time)` | `datetime.now(UTC)` |
