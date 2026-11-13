# Research: Chuẩn Hóa Thời Gian Xảy Ra Vi Phạm Tự Động Theo UTC

## Context & Objectives
Hiện tại các tác vụ định kỳ (background jobs chạy 23:59 hoặc hàng giờ) và event handlers khi tạo vi phạm tự động đều đang dùng `now = datetime.now(UTC)` để gán vào trường `date` của thực thể `Violation`.
Điều này dẫn đến:
1. Vi phạm ghi nhận sai ngày/giờ xảy ra sự việc (ví dụ buổi họp diễn ra 18:00 ngày 10/11, nhưng vi phạm ghi nhận 23:59 ngày 12/11 do job quét trễ 2 ngày).
2. Khi client hiển thị theo local timezone của người dùng trên UI, thời gian hiển thị là thời điểm chạy job nửa đêm chứ không phải thời điểm diễn ra buổi sinh hoạt/hạn nộp bài.

Mục tiêu nghiên cứu:
- Xác định nguồn mốc thời gian chuẩn (`occurrence datetime`) cho từng loại vi phạm.
- Xác định cách chuẩn hóa timezone-aware UTC (`ensure_utc` / `parse_to_utc`).
- Đánh giá ảnh hưởng tới logic chống trùng lặp (`get_by_user_and_date`, `exists_by_user_and_reason`).

---

## 1. Phân Tích Các Nguồn Vi Phạm Tự Động & Mốc Thời Gian Xảy Ra

### A. Vắng sinh hoạt (`ParticipantAbsenceRecorded` -> `_handle_meeting_absence`)
- **Nguồn kích hoạt**: Job điểm danh `CheckMeetingAttendanceUseCase` quét các buổi họp kết thúc cách đây 2 ngày (hoặc ngày chỉ định).
- **Hiện tại**: `_handle_meeting_absence` gán `date=now` (`datetime.now(UTC)`).
- **Mốc thời gian đúng**: Thời gian bắt đầu buổi họp `meeting.start_time`.
- **Giải pháp**:
  - Cập nhật Domain Event `ParticipantAbsenceRecorded` bổ sung trường `start_time: datetime | None = None`.
  - Trong `CheckMeetingAttendanceUseCase`: truyền `start_time=meeting.start_time` vào `ParticipantAbsenceRecorded`.
  - Trong `_handle_meeting_absence`: lấy `occurrence_date = ensure_utc(event.start_time) if event.start_time else datetime.now(UTC)`. Gán `date=occurrence_date`.

### B. Đi trễ sinh hoạt (`ParticipantLateRecorded` -> `_handle_meeting_late`)
- **Nguồn kích hoạt**: Job điểm danh `CheckMeetingAttendanceUseCase` hoặc khi quẹt thẻ check-in phát hiện trễ.
- **Hiện tại**: `_handle_meeting_late` gán `date=now` (`datetime.now(UTC)`).
- **Mốc thời gian đúng**: Thời gian học viên check-in thực tế `event.check_in_at` (thời điểm xảy ra hành vi đi trễ).
- **Giải pháp**:
  - `ParticipantLateRecorded` đã có sẵn trường `check_in_at: datetime`.
  - Trong `_handle_meeting_late`: lấy `occurrence_date = ensure_utc(event.check_in_at) if event.check_in_at else datetime.now(UTC)`. Gán `date=occurrence_date`.

### C. Quá hạn nộp bài tập (`HomeworkOverdueDetected` -> `_handle_homework_overdue`)
- **Nguồn kích hoạt**: Job bài tập `CheckOverdueHomeworkUseCase` quét các assignees có deadline ngày D (cách đây 2 ngày).
- **Hiện tại**: `_handle_homework_overdue` gán `date=now` (`datetime.now(UTC)`).
- **Mốc thời gian đúng**: Thời hạn nộp bài tập của học viên `assignment.deadline`.
- **Giải pháp**:
  - Cập nhật Domain Event `HomeworkOverdueDetected` bổ sung `deadline: datetime | None = None`.
  - Trong `CheckOverdueHomeworkUseCase`: truyền `deadline=assignment.deadline` vào `HomeworkOverdueDetected`.
  - Trong `_handle_homework_overdue`: lấy `occurrence_date = ensure_utc(event.deadline) if event.deadline else datetime.now(UTC)`. Gán `date=occurrence_date`.

### D. Quá hạn trực nhật (`CheckOverdueDutiesUseCase`)
- **Nguồn kích hoạt**: Job trực nhật `check_overdue_duties` chạy lúc 23:59.
- **Hiện tại**: `CheckOverdueDutiesUseCase` gọi `create_violation_use_case.execute(..., date=datetime.now(UTC))`.
- **Mốc thời gian đúng**:
  - Nếu ca trực gắn với buổi họp (`duty.meeting_id`): thời điểm kết thúc buổi họp `meeting.end_time` (hoặc `meeting.start_time`).
  - Nếu ca trực độc lập (theo ngày): thời điểm cuối ngày trực nhật `23:59:59` giờ Việt Nam, chuyển đổi sang UTC (tức `16:59:59 UTC` của ngày hôm đó).
- **Giải pháp**:
  - Nếu có `meeting` và `meeting.end_time`: `occurrence_date = ensure_utc(meeting.end_time)`.
  - Ngược lại: tính `end_of_duty_day_vn = datetime.combine(duty.duty_date, time(23, 59, 59))` -> `ensure_utc(end_of_duty_day_vn)`.
  - Truyền `date=occurrence_date` vào `create_violation_use_case.execute`.

### E. Quá hạn đánh giá buổi học 24h (`CheckEvaluationDeadlineJobUseCase`)
- **Nguồn kích hoạt**: Job `check_meeting_evaluations` chạy mỗi giờ.
- **Hiện tại**: Dùng `now = datetime.now(UTC)` khi tạo `Violation.create_system_violation(..., date=now)`.
- **Mốc thời gian đúng**: Thời điểm chính thức quá hạn 24h, tức là `meeting.end_time + timedelta(hours=24)` (chuẩn hóa UTC).
- **Giải pháp**:
  - Tính `deadline_24h = ensure_utc(meeting.end_time) + timedelta(hours=24)` (nếu có `meeting.end_time`), fallback về `now` nếu thiếu.
  - Truyền `date=deadline_24h` khi tạo violation.

### F. Xin phép vượt quá số lần quy định (`PermissionViolationHandler`)
- **Nguồn kích hoạt**: Sự kiện `PermissionRequestCreated`.
- **Hiện tại**: Dùng `date=datetime.now(UTC)`.
- **Mốc thời gian đúng**: `event.start_time` (thời điểm buổi họp/bài tập được xin phép vắng/hoãn) hoặc thời điểm tạo đơn nếu không có `start_time`.
- **Giải pháp**:
  - `occurrence_date = ensure_utc(event.start_time) if event.start_time else datetime.now(UTC)`.

---

## 2. Đánh Giá Khả Năng Trùng Lặp & Logic Idempotency Của Violation

### Phân tích `CreateViolationUseCase`
```python
if is_system:
    existing = self.repo.get_by_user_and_date(user_id, date)
    if any(v.reason == reason for v in existing):
        continue
```
`get_by_user_and_date` truy vấn theo `target_date.date()` (từ `start = 00:00:00` đến `end = 23:59:59` của ngày `date`).
- Khi ta đổi `date` từ thời điểm chạy job sang thời điểm xảy ra sự việc (`meeting.start_time`, `assignment.deadline`, etc.):
  - `date` bây giờ là một giá trị **xác định (deterministic)** gắn liền với sự kiện, thay vì biến động theo từng lần job chạy.
  - Khi job quét lại (re-scan) hoặc chạy lại cùng một ngày, `date` truyền vào là cố định.
  - Do đó, `existing = self.repo.get_by_user_and_date(user_id, date)` sẽ luôn kiểm tra chính xác các vi phạm xảy ra trong cùng ngày sự kiện và so khớp `reason`, ngăn chặn việc tạo trùng lặp một cách tự nhiên và ổn định hơn trước rất nhiều!

### Chú ý về timezone trong `get_by_user_and_date`
Trong `ViolationRepository`:
```python
d = target_date.date() if isinstance(target_date, datetime) else target_date
start = datetime.combine(d, time.min)
end = datetime.combine(d, time.max)
```
Cần lưu ý: Nếu `target_date` là UTC aware datetime, `start` và `end` phải được gán timezone UTC để truy vấn SQL với `DateTime(timezone=True)` không bị so sánh naive vs aware.
Cụ thể:
```python
if isinstance(target_date, datetime):
    # Nếu là timezone aware UTC, giữ nguyên d theo UTC
    d = target_date.date()
    start = datetime.combine(d, time.min, tzinfo=UTC)
    end = datetime.combine(d, time.max, tzinfo=UTC)
```

---

## 3. Quyết Định Thiết Kế (Design Decisions)

1. **Sử dụng `ensure_utc` từ `app.shared.domain.datetime_types`**:
   - Mọi mốc thời gian trước khi gán vào `date` của `Violation` đều đi qua `ensure_utc(...)`.
   - Nếu dữ liệu đã có `tzinfo`, chuyển về `astimezone(UTC)`. Nếu naive, mặc định coi là giờ Việt Nam (`Asia/Ho_Chi_Minh`) và chuyển sang UTC.

2. **Cập nhật Domain Events**:
   - `ParticipantAbsenceRecorded`: thêm `start_time: datetime | None = None`.
   - `HomeworkOverdueDetected`: thêm `deadline: datetime | None = None`.
   - Cả 2 đều tương thích hoàn toàn với các event listener khác (nếu có).

3. **Cập nhật Repository**:
   - Đảm bảo `get_by_user_and_date` trong `ViolationRepository` dùng timezone-aware UTC cho `start` và `end` bounds.

4. **Frontend**:
   - `ViolationTable.tsx` và các component khác đã dùng `dayjs(date).format('DD/MM/YYYY HH:mm')`. Dayjs tự động parse chuỗi ISO 8601 UTC và hiển thị theo local timezone của browser.
   - Thêm unit test hoặc kiểm tra format để đảm bảo hiển thị đúng.
