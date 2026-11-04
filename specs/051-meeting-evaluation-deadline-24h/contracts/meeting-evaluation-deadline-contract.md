# Hợp Đồng Giao Thức: Quy Tắc Vi Phạm Đánh Giá Cuộc Họp

**Feature**: `051-meeting-evaluation-deadline-24h`  
**Ngày**: 2026-11-05

---

## 1. Hợp Đồng Ngưỡng Thời Gian (Time Boundary Contract)

Tác vụ quét định kỳ gọi repository với các ngưỡng thời gian:
- **`now`**: `datetime.now(timezone.utc)`
- **`start_bound`**: `now - timedelta(days=MEETING_EVALUATION_SCAN_WINDOW_DAYS)` (mặc định 9 ngày)
- **`end_bound`**: `now - timedelta(hours=MEETING_EVALUATION_DEADLINE_HOURS)` (mới: 24 giờ)

**Điều kiện SQL của Repository**:
```sql
WHERE meetings.enable_evaluation = TRUE
  AND meetings.end_time >= :start_bound
  AND meetings.end_time <= :end_bound
```

---

## 2. Hợp Đồng Mẫu Văn Bản Vi Phạm (Violation Reason Text Contract)

Mọi văn bản lý do vi phạm được lưu trong cơ sở dữ liệu và thông báo cho người dùng PHẢI tuân thủ định dạng chuẩn sau:

| Đối tượng vi phạm | Định dạng chuỗi lý do vi phạm (`reason`) |
| :--- | :--- |
| **Học viên (Trainee)** | `Chưa hoàn thành đánh giá Trainer cho buổi học '{meeting.title}' ({time_range}) trong vòng 24h` |
| **Giảng viên (Trainer)** | `Trainer chưa hoàn tất đánh giá tổng thể buổi học '{meeting.title}' ({time_range}) trong vòng 24h` |

*Ghi chú*: `{time_range}` là khoảng thời gian định dạng dạng `(HH:MM - HH:MM, DD/MM/YYYY)` hoặc rỗng nếu không có thời gian.

---

## 3. Hợp Đồng Đăng Ký Tác Vụ Lập Lịch (Scheduler Job Contract)

Trong `backend/app/core/scheduler.py`:
- **Job ID**: `meeting_evaluation_check`
- **Job Name**: `Check 24h meeting evaluations deadline`
- **Trigger**: `CronTrigger(minute=0, timezone="Asia/Ho_Chi_Minh")` (chạy mỗi giờ 1 lần tại phút 00)
