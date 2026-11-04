# Quickstart Validation Guide: Pure Countdown Offsets & Mute Zalo Bot

**Feature**: `047-reduce-reminder-spam`  
**Date**: 2026-11-04  
**Scope**: Automated Unit & Integration Verification  

---

## 1. Prerequisites (Tiền điều kiện)

1. Môi trường Python 3.12+ được quản lý bởi `uv`.
2. Toàn bộ dependencies được cài đặt trong thư mục `backend/`:
   ```bash
   cd backend
   uv sync
   ```

---

## 2. Validation Scenarios (Kịch bản kiểm chứng tự động)

### Kịch bản 1: Kiểm chứng Loại bỏ 4 Khung Giờ Cố Định (No Fixed Hours)
- **Mục tiêu**: Chứng minh rằng vào các khung giờ `08:00`, `12:00`, `19:30`, `22:00`, hệ thống KHÔNG còn tự động sinh ra các mốc `FIXED_0800`, `FIXED_1200`, `FIXED_1930`, `FIXED_2200`.
- **Lệnh thực thi**:
  ```bash
  cd backend && uv run pytest tests/unit/test_reminder_use_cases.py -k "test_calculate_matching_stages_no_fixed_hours"
  ```
- **Kết quả kỳ vọng**:
  - Khi `now` là 08:00, 12:00, 19:30 hoặc 22:00 nhưng khoảng cách đến deadline không rơi vào mốc đếm ngược (24h, 4h, 1h), `calculate_matching_stages()` trả về danh sách rỗng `[]`.

---

### Kịch bản 2: Kiểm chứng 3 Mốc Đếm Ngược Chuẩn (Pure Countdown Offsets: 24h, 4h, 1h)
- **Mục tiêu**: Chứng minh 3 mốc đếm ngược kích hoạt chính xác theo khoảng cách đến deadline.
- **Lệnh thực thi**:
  ```bash
  cd backend && uv run pytest tests/unit/test_reminder_use_cases.py -k "test_calculate_matching_stages_offsets"
  ```
- **Kết quả kỳ vọng**:
  - `diff_hours = 24.0` ➔ Trả về `[ReminderStage.OFFSET_1D]`.
  - `diff_hours = 4.0` ➔ Trả về `[ReminderStage.OFFSET_4H]`.
  - `diff_hours = 1.0` ➔ Trả về `[ReminderStage.OFFSET_1H]`.
  - `diff_hours = 48.0` (mốc 2 ngày cũ) ➔ Trả về `[]` (đã bỏ mốc `OFFSET_2D`).
  - `diff_hours = 12.0` (mốc 12h cũ) ➔ Trả về `[]` (đã bỏ mốc `OFFSET_12H`).

---

### Kịch bản 3: Kiểm chứng Mute Kênh Zalo Bot
- **Mục tiêu**: Chứng minh khi phát thông báo, kênh Zalo Bot bị bỏ qua (không gọi `send_message` của `ZaloBotClient`), trong khi In-App, Discord và Web Push vẫn hoạt động bình thường.
- **Lệnh thực thi**:
  ```bash
  cd backend && uv run pytest tests/unit/test_reminder_use_cases.py -k "test_zalo_channel_muted"
  ```
- **Kết quả kỳ vọng**:
  - `ZaloBotClient.send_message` không được gọi.
  - Kết quả phân phối cho Zalo trả về `status="DISABLED"`.

---

### Kịch bản 4: Chạy toàn bộ Test Suite của Reminder Module
- **Mục tiêu**: Bảo đảm không có hồi quy (Zero Regression) trên toàn bộ hệ thống Reminder và Notification.
- **Lệnh thực thi**:
  ```bash
  cd backend && uv run pytest tests/unit/test_reminder_use_cases.py tests/integration/test_reminder_integration.py
  ```
- **Kết quả kỳ vọng**:
  - 100% tests vượt qua (`passed`), không có lỗi syntax, không có `ValueError` liên quan đến `ReminderStage`.
