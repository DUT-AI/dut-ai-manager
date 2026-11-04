# Data Model & Domain Entities: Pure Countdown Offsets & Notification Channel Controls

**Feature**: `047-reduce-reminder-spam`  
**Date**: 2026-11-04  
**Layer**: Domain & Infrastructure  

---

## 1. Domain Entities & Value Objects

### 1.1. `ReminderStage` (Enum)
Đại diện cho các mốc thời gian nhắc nhở hạn chót của hệ thống.

```python
class ReminderStage(str, Enum):
    # ================= Active Pure Countdown Stages =================
    OFFSET_1D = "OFFSET_1D"  # 24 giờ trước hạn chót (Cửa sổ 22h - 26h)
    OFFSET_4H = "OFFSET_4H"  # 4 giờ trước hạn chót (Cửa sổ 3.5h - 4.5h)
    OFFSET_1H = "OFFSET_1H"  # 1 giờ trước hạn chót (Cửa sổ 0.5h - 1.5h) - Critical

    # ================= Deprecated Legacy Stages =====================
    # Giữ lại để đảm bảo tương thích ngược (Backward Compatibility)
    # khi đọc dữ liệu lịch sử từ bảng `notifications` trong PostgreSQL.
    # Tuyệt đối không sinh ra các giá trị này trong logic mới.
    OFFSET_2D = "OFFSET_2D"
    OFFSET_12H = "OFFSET_12H"
    FIXED_0800 = "FIXED_0800"
    FIXED_1200 = "FIXED_1200"
    FIXED_1930 = "FIXED_1930"
    FIXED_2200 = "FIXED_2200"

    @property
    def is_critical(self) -> bool:
        """Chỉ duy nhất mốc 1 giờ được coi là mốc khẩn cấp (Critical Level)."""
        return self == ReminderStage.OFFSET_1H
```

#### Quy tắc tính toán mốc (`calculate_matching_stages`):
- **Đầu vào**: `deadline: datetime`, `now: datetime`.
- **Chuẩn hóa**: Chuyển đổi cả `deadline` và `now` về UTC-aware.
- **Tính toán khoảng cách**: `diff_hours = (deadline_utc - now_utc).total_seconds() / 3600.0`.
- **Quy tắc khớp mốc**:
  1. `22.0 <= diff_hours <= 26.0` ➔ Trả về `[ReminderStage.OFFSET_1D]`
  2. `3.5 <= diff_hours <= 4.5` ➔ Trả về `[ReminderStage.OFFSET_4H]`
  3. `0.5 <= diff_hours <= 1.5` ➔ Trả về `[ReminderStage.OFFSET_1H]`
  4. Mọi trường hợp khác ➔ Trả về danh sách rỗng `[]`.

---

### 1.2. `Notification` (Domain Entity)
Đại diện cho bản ghi thông báo đã được lưu trữ trong cơ sở dữ liệu.

| Trường | Kiểu dữ liệu | Mô tả | Quy tắc nghiệp vụ |
|---|---|---|---|
| `id` | `int \| None` | Khóa chính tự tăng | Sinh tự động bởi DB |
| `user_id` | `int` | ID người nhận | Bắt buộc (Non-null) |
| `title` | `str` | Tiêu đề thông báo | Bắt buộc |
| `content` | `str` | Nội dung thông báo | Bắt buộc |
| `category` | `NotificationCategory` | Danh mục thông báo | `HOMEWORK`, `DUTY`, `MEETING`, `VIOLATION`, v.v. |
| `level` | `NotificationLevel` | Mức độ cảnh báo | `INFO`, `WARNING`, `CRITICAL` (Mốc 1h là `CRITICAL`) |
| `task_type` | `TaskType \| None` | Loại task liên quan | `HOMEWORK`, `DUTY`, `MEETING`, `MEETING_EVALUATION` |
| `task_id` | `int \| None` | ID của task | Dùng cho Deduplication |
| `reminder_stage`| `ReminderStage \| None` | Mốc đếm ngược | Lưu mốc `OFFSET_1D`, `OFFSET_4H`, `OFFSET_1H` |
| `is_read` | `bool` | Trạng thái đọc | Mặc định `False` |
| `read_at` | `datetime \| None` | Thời điểm đọc | Cập nhật khi đánh dấu đã đọc |
| `discord_status`| `ReminderStatus \| None` | Trạng thái gửi Discord | `SENT`, `FAILED`, `DM_BLOCKED`, v.v. |
| `zalo_status` | `ReminderStatus \| None` | Trạng thái gửi Zalo | Ghi nhận `None` hoặc `DISABLED` khi tắt kênh |
| `web_push_status`| `ReminderStatus \| None` | Trạng thái gửi Web Push | `SENT`, `FAILED`, `NO_SUBSCRIPTION` |

---

## 2. Channel Configuration Model

### 2.1. Cờ cấu hình Môi trường (`app.core.config.Settings`)
```python
ENABLE_ZALO_NOTIFICATION: bool = False  # Bật/tắt phân phối thông báo qua Zalo Bot
```

### 2.2. Trạng thái phân phối kênh (`ChannelDeliveryResult`)
Khi kênh Zalo Bot bị tắt:
- Kênh không được đưa vào danh sách dispatch hoặc trả về trạng thái:
```python
ChannelDeliveryResult(
    channel=ChannelType.ZALO,
    success=True,
    status="DISABLED",
    error_message=None
)
```

---

## 3. Quy trình Vòng đời Nhắc việc (Lifecycle State Machine)

```
[Nhiệm vụ được tạo]
        │
        ▼ (Hạn chót còn xa > 26h: Không gửi thông báo, người dùng xem trên Web)
        │
        ▼ (Thời gian chạm khoảng 24h: 22h <= diff <= 26h)
[Mốc OFFSET_1D: Gửi thông báo nhắc sớm (Warning)]
        │ (Lưu vào bảng notifications chống gửi trùng)
        ▼ (Thành viên chưa nộp bài, thời gian trôi đến 4h trước hạn: 3.5h <= diff <= 4.5h)
[Mốc OFFSET_4H: Gửi cảnh báo mức cao (Warning)]
        │ (Lưu vào bảng notifications chống gửi trùng)
        ▼ (Thành viên chưa nộp bài, thời gian trôi đến 1h trước hạn: 0.5h <= diff <= 1.5h)
[Mốc OFFSET_1H: Gửi cảnh báo khẩn cấp (Critical)]
        │
        ▼ (Hết hạn lúc 23:59)
[Overdue Checker chạy ghi nhận Vi phạm nếu vẫn chưa hoàn thành]
```

*Lưu ý*: Bất cứ thời điểm nào thành viên nộp bài / nộp minh chứng, trạng thái `is_submitted` hoặc trạng thái hoàn thành chuyển thành `True` ➔ Các mốc đếm ngược tiếp theo lập tức bỏ qua.
