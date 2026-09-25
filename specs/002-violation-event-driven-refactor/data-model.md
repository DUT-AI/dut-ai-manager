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

---

## 3. Cấu Trúc Phân Tách Use Case (1 File / 1 Use Case)

### Domain Violation (`backend/app/violation/application/`):
- `create_violation_use_case.py` -> `CreateViolationUseCase` (Tạo vi phạm hệ thống / thủ công, phát `ViolationCreated`)
- `get_violations_use_case.py` -> `GetViolationsUseCase` (Truy vấn vi phạm theo tháng, user, khoảng ngày)
- `update_violation_use_case.py` -> `UpdateViolationUseCase` (Cập nhật lý do, ngày vi phạm)
- `delete_violation_use_case.py` -> `DeleteViolationUseCase` (Xóa mềm vi phạm)
- `restore_violation_use_case.py` -> `RestoreViolationUseCase` (Khôi phục vi phạm đã xóa mềm)
- `__init__.py` -> Re-export 5 use cases trên.

### Domain Meeting (`backend/app/meeting/application/`):
- `create_meeting_use_case.py` -> `CreateMeetingUseCase` (Tạo buổi họp, gán participants)
- `get_meetings_use_case.py` -> `GetMeetingsUseCase` (Lấy danh sách / chi tiết meeting theo ngày, user, team)
- `update_meeting_use_case.py` -> `UpdateMeetingUseCase` (Cập nhật thông tin cuộc họp)
- `delete_meeting_use_case.py` -> `DeleteMeetingUseCase` (Xóa cuộc họp)
- `checkin_use_case.py` -> `CheckInUseCase` (Check-in qua ảnh/tọa độ)
- `checkin_with_card_use_case.py` -> `CheckInWithCardUseCase` (Check-in qua mã thẻ RFID/NFC)
- `checkout_use_case.py` -> `CheckOutUseCase` (Check-out buổi họp)
- `check_meeting_attendance_use_case.py` -> `CheckMeetingAttendanceUseCase` (Đánh giá điểm danh & phát sự kiện vắng/trễ)
- `update_participant_status_use_case.py` -> `UpdateParticipantStatusUseCase` (Cập nhật thủ công trạng thái thành viên)
- `calculate_current_capacity_use_case.py` -> `CalculateCurrentCapacityUseCase` (Tính tải và capacity phòng họp)
- `__init__.py` -> Re-export 10 use cases trên.

```
