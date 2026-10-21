# Data Model Design: Upcoming Meeting Attendance Reminder

**Feature**: `023-upcoming-meeting-reminder`  
**Date**: 2026-10-21  
**Spec**: [spec.md](./spec.md) | **Research**: [research.md](./research.md)

---

## 1. Domain Model Entities & Enums

### 1.1 TaskType Enum Extension
Được định nghĩa tại `backend/app/reminder/domain/entity.py`.

```python
class TaskType(str, Enum):
    HOMEWORK = "HOMEWORK"
    DUTY = "DUTY"
    MEETING_EVALUATION = "MEETING_EVALUATION"
    MEETING = "MEETING"  # Mới: Nhắc nhở buổi họp / sinh hoạt sắp diễn ra
```

### 1.2 Candidate Task Item (Data Transfer Value Object)
Được định nghĩa tại `backend/app/reminder/application/scanners/base_scanner.py`.

```python
@dataclass
class ScannedCandidateTask:
    task_type: TaskType         # TaskType.MEETING
    task_id: int                # ID của buổi họp (meeting.id)
    task_title: str             # Tên buổi họp: f"Cuộc họp: {meeting.title}"
    user_id: int                # ID người dùng cần nhắc nhở (participant.user_id)
    deadline: datetime          # Thời điểm bắt đầu cuộc họp (meeting.start_time)
    action_url: str             # f"/dashboard/meetings/{meeting.id}"
    stages: list[ReminderStage] # Danh sách các mốc ReminderStage kích hoạt
```

### 1.3 Notification Entity Mapping
Thực thể `Notification` trong `backend/app/reminder/domain/entity.py`:

| Thuộc tính | Kiểu dữ liệu | Giá trị cho Buổi họp | Mô tả |
|---|---|---|---|
| `user_id` | `int` | `participant.user_id` | Khóa ngoại người nhận |
| `title` | `str` | `Nhắc nhở cuộc họp sắp diễn ra: {meeting.title}` | Tiêu đề hiển thị |
| `content` | `str` | `Cuộc họp {title} sẽ bắt đầu lúc {start_time} (còn lại {time_left})...` | Nội dung chi tiết |
| `category` | `NotificationCategory` | `NotificationCategory.MEETING` | Phân loại thông báo |
| `level` | `NotificationLevel` | `CRITICAL` nếu là mốc `OFFSET_1H`, ngược lại là `WARNING` | Cấp độ khẩn cấp |
| `action_url` | `str` | `/dashboard/meetings/{meeting.id}` | Link điều hướng |
| `is_read` | `bool` | `False` | Trạng thái đọc |
| `task_type` | `TaskType` | `TaskType.MEETING` | Metadata kỹ thuật chống trùng |
| `task_id` | `int` | `meeting.id` | ID bản ghi cuộc họp |
| `reminder_stage`| `ReminderStage` | `OFFSET_1D`, `OFFSET_1H`, `FIXED_0800`, v.v. | Mốc thời gian được quét |
| `discord_status`| `ReminderStatus` | `SENT` / `FAILED` / `NO_DISCORD_ID` / `DM_BLOCKED` | Kết quả gửi Discord Bot DM |
| `created_at` | `datetime` | `now` (UTC+7) | Thời điểm ghi nhận |

---

## 2. Participant Status Filtering Logic

| Trạng thái Participant (`ParticipantStatus`) | Điều kiện lọc | Hành động của Scanner | Lý do |
|---|---|---|---|
| `NOT_JOINED` | `is_deleted == False` | **NHẮC NHỞ** | Thành viên có lịch nhưng chưa điểm danh |
| `ABSENT_EXCUSED` | Bất kỳ | **BỎ QUA** | Đã được duyệt đơn xin nghỉ phép hợp lệ |
| `JOINED` | Bất kỳ | **BỎ QUA** | Đã thực hiện điểm danh trước giờ họp |
| `COMPLETED` | Bất kỳ | **BỎ QUA** | Buổi họp/ca sinh hoạt của người này đã hoàn tất |
| `is_deleted == True` | `is_deleted == True` | **BỎ QUA** | Người tham gia đã bị xóa khỏi buổi họp |
| `LATE_EXCUSED` | Đã check-in (`check_in_at is not None`) | **BỎ QUA** | Đã có mặt tại buổi họp |
| `LATE_EXCUSED` | Chưa check-in (`check_in_at is None`) | **NHẮC NHỞ** | Xin phép đi trễ nhưng chưa có mặt |

---

## 3. Database Schema (No Schema Changes Required)

Bảng cơ sở dữ liệu `notifications` hiện tại (được tạo từ Spec 019) đã hỗ trợ đầy đủ các trường:
- `task_type VARCHAR(50)`
- `task_id INTEGER`
- `category VARCHAR(50)`
- `reminder_stage VARCHAR(50)`
- `discord_status VARCHAR(50)`
- `action_url VARCHAR(255)`

Index đa cột đã có sẵn:
- `idx_notifications_dedup ON notifications (task_type, task_id, user_id, reminder_stage)`
- `idx_notifications_user_category ON notifications (user_id, category, is_read)`

$\rightarrow$ **Không cần tạo thêm bất kỳ migration Alembic nào mới.**
