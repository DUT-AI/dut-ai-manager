# Quickstart: Hướng Dẫn Kiểm Thử & Xác Thực Refactor Event-Driven Violation

## 1. Mục tiêu kiểm thử
Xác thực rằng việc chuyển đổi sang mô hình Event-Driven không làm gián đoạn luồng xử lý vi phạm, không để lọt vi phạm và triệt tiêu hoàn toàn import chéo giữa các domain.

---

## 2. Kịch bản xác thực tự động (Automated Test Scenarios)

### Kịch bản 1: Kiểm tra vắng họp không phép ➔ Tự tạo Vi phạm qua EventBus
- **File test**: `backend/tests/test_meeting_violation_event_driven.py`
- **Các bước**:
  1. Tạo 1 Mock Meeting có `require_check_in=True` diễn ra hôm nay.
  2. Gán 1 Participant chưa check-in và không có đơn xin phép.
  3. Chạy `CheckMeetingAttendanceUseCase.execute()`.
  4. **Kỳ vọng**:
     - `CheckMeetingAttendanceUseCase` phát ra sự kiện `ParticipantAbsenceRecorded`.
     - `AutomatedViolationHandler` nhận sự kiện, tra cứu đơn (kết quả: không có) và tạo 01 `ViolationModel`.
     - `Participant` được cập nhật trạng thái `ABSENT_UNEXCUSED`.

---

### Kịch bản 2: Kiểm tra vắng họp CÓ PHÉP ➔ Miễn trừ vi phạm
- **Các bước**:
  1. Tạo 1 Mock Meeting + 1 Participant chưa check-in.
  2. Tạo 1 `PermissionRequest` loại `ABSENCE` đã duyệt cho user.
  3. Chạy `CheckMeetingAttendanceUseCase.execute()`.
  4. **Kỳ vọng**:
     - `Participant` được cập nhật trạng thái `ABSENT_EXCUSED`.
     - KHÔNG có bất kỳ bản ghi `ViolationModel` nào được tạo.

---

### Kịch bản 3: Kiểm tra khớp nối mã nguồn (Static Architecture Guard)
- **Lệnh chạy**:
  ```bash
  # Kiểm tra xem còn import chéo nào từ Meeting sang Violation không
  grep -r "from app.violation" backend/app/meeting/
  ```
- **Kỳ vọng**: Không có kết quả nào trả về (0 imports).

---

### Kịch bản 4: Kiểm tra cấu trúc Single-Responsibility Use Cases (1 File / 1 Use Case)
- **Lệnh chạy**:
  ```bash
  # Kiểm tra không còn file gom chung use_cases.py / crud_use_cases.py trong meeting và violation
  ls backend/app/violation/application/create_violation_use_case.py backend/app/violation/application/get_violations_use_case.py
  ls backend/app/meeting/application/create_meeting_use_case.py backend/app/meeting/application/get_meetings_use_case.py
  ```
- **Kỳ vọng**: Mỗi Use Case nằm ở file riêng và `__init__.py` export đầy đủ.

---

## 3. Lệnh chạy toàn bộ Test Suite
```bash
pytest backend/tests/ -v
```
