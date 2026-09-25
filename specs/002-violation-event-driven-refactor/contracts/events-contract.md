# Event Contracts: Decoupled Domain Events

## 1. Scope
Tài liệu này định nghĩa giao ước dữ liệu (Interface Contract) giữa các domain phát sự kiện (`Meeting`, `Homework`) và domain tiếp nhận xử lý (`Violation`).

---

## 2. Event Specifications

### Contract 1: `ParticipantAbsenceRecorded`
- **Tên lớp**: `app.meeting.domain.events.ParticipantAbsenceRecorded`
- **Kế thừa**: `app.shared.domain.event_bus.DomainEvent`
- **Payload Schema**:
  ```json
  {
    "user_id": 123,
    "meeting_id": 456,
    "meeting_title": "Sinh hoạt Lab định kỳ tuần 38",
    "meeting_date": "2026-09-25"
  }
  ```
- **Quy tắc bảo đảm (Invariants)**:
  - `user_id` và `meeting_id` là số nguyên dương hợp lệ.
  - `meeting_date` theo chuẩn ISO format `YYYY-MM-DD`.

---

### Contract 2: `ParticipantLateRecorded`
- **Tên lớp**: `app.meeting.domain.events.ParticipantLateRecorded`
- **Kế thừa**: `app.shared.domain.event_bus.DomainEvent`
- **Payload Schema**:
  ```json
  {
    "user_id": 123,
    "meeting_id": 456,
    "meeting_title": "Sinh hoạt Lab định kỳ tuần 38",
    "check_in_at": "2026-09-25T14:12:00",
    "start_time": "2026-09-25T14:00:00"
  }
  ```
- **Quy tắc bảo đảm (Invariants)**:
  - `check_in_at` và `start_time` là `datetime` naive theo múi giờ UTC+7.
  - `check_in_at > start_time + timedelta(minutes=5)`.

---

### Contract 3: `HomeworkOverdueDetected`
- **Tên lớp**: `app.homework.domain.value_objects.HomeworkOverdueDetected`
- **Kế thừa**: `app.shared.domain.event_bus.DomainEvent`
- **Payload Schema**:
  ```json
  {
    "user_id": 123,
    "homework_id": 789,
    "homework_title": "Bài tập Python Asyncio",
    "deadline_date": "2026-09-25",
    "reason": "Chưa hoàn thành bài tập coding (Bài tập Python Asyncio) và không phép"
  }
  ```
