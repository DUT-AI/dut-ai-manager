# Quickstart & Validation Guide: Chuẩn Hóa Thời Gian Vi Phạm UTC

Hướng dẫn kịch bản kiểm thử và xác thực tính năng chuẩn hóa thời gian vi phạm tự động theo UTC.

## Prerequisites

1. Đã cài đặt môi trường backend:
   ```bash
   cd backend
   source .venv/bin/activate  # hoặc poetry shell / uv run
   ```
2. Đã chạy service database/redis (nếu chạy tích hợp) hoặc chạy pytest với SQLite/Mock.

## Test Scenarios

### Kịch bản 1: Kiểm tra tạo vi phạm vắng sinh hoạt
- **Mô tả**: Buổi họp bắt đầu lúc `2026-11-10 18:00:00+07:00` (`2026-11-10 11:00:00 UTC`). Học viên không check-in.
- **Thực thi**:
  Chạy `CheckMeetingAttendanceUseCase` và lắng nghe sự kiện `ParticipantAbsenceRecorded` qua `AutomatedViolationHandler`.
- **Kết quả mong đợi**:
  Bản ghi `Violation` được tạo có:
  - `date`: `2026-11-10 11:00:00+00:00` (UTC)
  - `reason`: `Vắng sinh hoạt: ... (Không xin phép)`
  - Khi format trên client `dayjs(date).format('DD/MM/YYYY HH:mm')` -> `10/11/2026 18:00`.

### Kịch bản 2: Kiểm tra tạo vi phạm đi trễ
- **Mô tả**: Buổi họp bắt đầu lúc 18:00. Học viên check-in lúc `2026-11-10 18:25:00+07:00` (`2026-11-10 11:25:00 UTC`) mà không có phép.
- **Thực thi**:
  Phát sự kiện `ParticipantLateRecorded(check_in_at=datetime(2026, 11, 10, 11, 25, tzinfo=UTC), ...)`.
- **Kết quả mong đợi**:
  Bản ghi `Violation` được tạo có:
  - `date`: `2026-11-10 11:25:00+00:00` (UTC)
  - Khi format trên client -> `10/11/2026 18:25`.

### Kịch bản 3: Kiểm tra tạo vi phạm bài tập quá hạn
- **Mô tả**: Bài tập có deadline là `2026-11-10 23:59:00+07:00` (`2026-11-10 16:59:00 UTC`). Học viên chưa nộp. Job chạy vào ngày 12/11.
- **Thực thi**:
  Chạy `CheckOverdueHomeworkUseCase` cho ngày `2026-11-10`.
- **Kết quả mong đợi**:
  Bản ghi `Violation` được tạo có:
  - `date`: `2026-11-10 16:59:00+00:00` (UTC)
  - `created_at`: Thời điểm chạy job ngày 12/11.

### Kịch bản 4: Kiểm tra trực nhật và đánh giá 24h
- **Mô tả**:
  - Trực nhật: Buổi học kết thúc lúc 19:30 ngày 10/11 -> vi phạm có `date` là `2026-11-10 12:30:00 UTC`.
  - Đánh giá 24h: Buổi học kết thúc lúc 19:30 ngày 10/11 -> vi phạm có `date` là `2026-11-11 12:30:00 UTC` (`end_time + 24h`).

## Run Unit Tests
```bash
pytest backend/tests/test_violation.py
pytest backend/tests/meeting/test_meeting_attendance.py
pytest backend/tests/homework/test_homework_overdue.py
```
