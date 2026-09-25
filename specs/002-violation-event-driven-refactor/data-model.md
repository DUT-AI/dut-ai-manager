# Phase 1: Data Model & Domain Event Schemas

## 1. Domain Event Schemas

### `ParticipantAbsenceRecorded` (Phát từ domain Meeting)
Sự kiện thành viên không thực hiện điểm danh khi buổi họp kết thúc hoặc khi Job 23:59 quét.
```python
class ParticipantAbsenceRecorded(DomainEvent):
    user_id: int
    meeting_id: int
    meeting_title: str
    meeting_date: str  # YYYY-MM-DD
```

### `ParticipantLateRecorded` (Phát từ domain Meeting)
Sự kiện thành viên thực hiện điểm danh muộn hơn thời gian quy định (> 5 phút so với `start_time`).
```python
class ParticipantLateRecorded(DomainEvent):
    user_id: int
    meeting_id: int
    meeting_title: str
    check_in_at: datetime
    start_time: datetime
```

### `HomeworkOverdueDetected` (Phát từ domain Homework)
Sự kiện thành viên chưa hoàn thành bài tập khi đến hạn chót (deadline).
```python
class HomeworkOverdueDetected(DomainEvent):
    user_id: int
    homework_id: int
    homework_title: str
    deadline_date: str  # YYYY-MM-DD
    uncompleted_items: list[str]  # ["coding", "game"]
    reason: str | None = None
```

---

## 2. Luồng Chuyển Trạng Thái (State Transitions)

### Trong Domain Meeting:
```text
[NOT_JOINED] ──(Job 23:59 / Meeting kết thúc)──> Phát ParticipantAbsenceRecorded
[CHECKIN_LATE] ──(Check-in > start + 5p)────────> Phát ParticipantLateRecorded
[CHECKIN_ON_TIME] ──────────────────────────────> Set status = JOINED / COMPLETED (Không phát event vi phạm)
```

### Trong Domain Violation:
```text
Khi nhận ParticipantAbsenceRecorded:
  1. Kiểm tra PermissionRequest (category=ABSENCE, user_id, meeting_id/date, status=APPROVED).
  2. NẾU CÓ ĐƠN HỢP LỆ:
     - Cập nhật ParticipantStatus = ABSENT_EXCUSED.
     - KHÔNG tạo Violation.
  3. NẾU KHÔNG CÓ ĐƠN:
     - Cập nhật ParticipantStatus = ABSENT_UNEXCUSED.
     - TẠO Violation: "Vắng sinh hoạt: {meeting_title} (Không xin phép)".

Khi nhận ParticipantLateRecorded:
  1. Kiểm tra PermissionRequest (category=LATE, user_id, meeting_id/date, status=APPROVED).
  2. NẾU CÓ ĐƠN & check_in_at <= đơn.start_time:
     - Cập nhật ParticipantStatus = LATE_EXCUSED.
     - KHÔNG tạo Violation.
  3. NẾU KHÔNG CÓ ĐƠN HOẶC ĐẾN MUỘN HƠN GIỜ XIN PHÉP:
     - Cập nhật ParticipantStatus = LATE_UNEXCUSED.
     - TẠO Violation: "Đi trễ sinh hoạt: {meeting_title} (Không xin phép)".

Khi nhận HomeworkOverdueDetected:
  1. Kiểm tra PermissionRequest (category=POSTPONE, user_id, homework_id, status=APPROVED).
  2. NẾU CÓ ĐƠN HỢP LỆ & now <= đơn.start_time:
     - KHÔNG tạo Violation.
  3. NẾU KHÔNG CÓ ĐƠN HOẶC QUÁ HẠN XIN HOÃN:
     - TẠO Violation: "Chưa hoàn thành {uncompleted_items} ({homework_title})".
```
