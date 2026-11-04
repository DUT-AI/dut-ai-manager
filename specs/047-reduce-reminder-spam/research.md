# Research & Architectural Decisions: Tái cấu trúc Nghiệp vụ Nhắc nhở & Tắt Kênh Zalo Bot

**Feature**: `047-reduce-reminder-spam`  
**Date**: 2026-11-04  
**Status**: Completed  

---

## 1. Nghiên cứu & Quyết định 1: Cơ chế Kích hoạt Nhắc nhở (Pure Countdown Offsets vs Fixed Hours)

### Vấn đề (Context)
Cơ chế cũ kết hợp cả 4 khung giờ cố định (`08:00`, `12:00`, `19:30`, `22:00`) và 5 mốc đếm ngược (`OFFSET_2D`, `OFFSET_1D`, `OFFSET_12H`, `OFFSET_4H`, `OFFSET_1H`). Khi một bài tập được giao trước 3 ngày, học viên bị réo liên tục 4 lần mỗi ngày bất kể deadline còn xa. Đến ngày cuối cùng, các mốc đếm ngược tiếp tục kích hoạt song song với các khung giờ cố định, dẫn đến tình trạng "bão thông báo" (notification flood).

### Quyết định (Decision)
1. **Loại bỏ hoàn toàn logic quét theo 4 khung giờ cố định** (`FIXED_0800`, `FIXED_1200`, `FIXED_1930`, `FIXED_2200`).
2. **Chuyển 100% sang cơ chế Thuần Đếm Ngược (Pure Countdown Offsets)** với 3 mốc chuẩn:
   - **Mốc 24h (`OFFSET_1D`)**: Nhắc nhở cảnh báo sớm khi hạn chót còn trong khoảng 22.0h – 26.0h.
   - **Mốc 4h (`OFFSET_4H`)**: Nhắc nhở cảnh báo mức cao (Warning) khi hạn chót còn trong khoảng 3.5h – 4.5h.
   - **Mốc 1h (`OFFSET_1H`)**: Cảnh báo nguy cấp cuối cùng (Critical) khi hạn chót còn trong khoảng 0.5h – 1.5h.
3. **Loại bỏ các mốc đếm ngược dư thừa**: `OFFSET_2D` (48h) và `OFFSET_12H` (12h) không còn được sinh ra trong hàm tính toán `calculate_matching_stages`.
4. **Bảo toàn tương thích ngược cho dữ liệu cũ (Backward Compatibility)**:
   - Giữ lại các thành viên cũ trong enum `ReminderStage` (hoặc xử lý fallback) để khi truy vấn các bản ghi `notifications` cũ trong lịch sử database không gây lỗi `ValueError: 'FIXED_0800' is not a valid ReminderStage`.
   - Trong logic nghiệp vụ tính toán mới `calculate_matching_stages`, chỉ sinh ra 3 giá trị: `OFFSET_1D`, `OFFSET_4H`, `OFFSET_1H`.

### Rationale
- Mỗi nhiệm vụ từ khi tạo đến khi kết thúc chỉ kích hoạt tối đa đúng 3 lần thông báo (thay vì 15-20 lần như trước).
- Độ bao phủ xung quanh chu kỳ quét 30 phút của Scheduler:
  - Mốc 24h: Cửa sổ 4 giờ (22h - 26h) đảm bảo Scheduler chạy mỗi 30 phút chắc chắn bắt được ít nhất 1 lần, kết hợp cơ chế Deduplication chỉ gửi đúng 1 lần.
  - Mốc 4h: Cửa sổ 1 giờ (3.5h - 4.5h) đảm bảo ít nhất 2 chu kỳ quét quét trúng, deduplication ngăn gửi lặp.
  - Mốc 1h: Cửa sổ 1 giờ (0.5h - 1.5h) đảm bảo ít nhất 2 chu kỳ quét quét trúng, deduplication ngăn gửi lặp.
- Người dùng không bao giờ bị đánh thức lúc 22:00 đêm theo lịch cố định vô nghĩa.

### Giải pháp thay thế đã xem xét (Alternatives Considered)
- *Giữ 2 khung giờ cố định (08:30 và 19:00)*: Bị người dùng từ chối vì vẫn gây cảm giác định kỳ máy móc.
- *Xóa bỏ hoàn toàn enum `FIXED_*` khỏi Python code*: Bị bác bỏ vì vi phạm Hiến pháp Principle V (Backward Compatibility) và làm crash API khi đọc lịch sử thông báo cũ trong DB PostgreSQL.

---

## 2. Nghiên cứu & Quyết định 2: Chiến lược Vô hiệu hóa Kênh Zalo Bot (Mute Zalo Bot without Deleting Code)

### Vấn đề (Context)
Người dùng yêu cầu: *"Bỏ zalobot, chỉ không thông báo báo zalobot nữa, chứ đừng xóa code nhé"*.
Hệ thống hiện tại có module Zalo hoàn chỉnh: `ZaloBotClient`, `ZaloNotificationChannel`, và các luồng liên kết webhook.

### Quyết định (Decision)
1. Thêm cấu hình điều khiển kênh thông báo trong `app.core.config.Settings`:
   ```python
   ENABLE_ZALO_NOTIFICATION: bool = False
   ```
   Mặc định là `False` (hoặc cấu hình thông qua biến môi trường).
2. Tại tầng điều phối trung tâm `UnifiedNotificationDispatcher`:
   - Kiểm tra `settings.ENABLE_ZALO_NOTIFICATION`. Khi bằng `False`, kênh `ZaloNotificationChannel` không được thêm vào danh sách các kênh ngoại vi cần phát tán `_external_channels` (hoặc được bypass).
3. Tại `ZaloNotificationChannel.send`:
   - Nếu được gọi trực tiếp, kiểm tra cờ `ENABLE_ZALO_NOTIFICATION`. Nếu `False`, trả về ngay kết quả an toàn:
     ```python
     ChannelDeliveryResult(channel=ChannelType.ZALO, success=True, status="DISABLED")
     ```
4. **Bảo toàn nguyên vẹn mã nguồn**:
   - Toàn bộ file `zalo_channel.py`, `zalo_bot_client.py`, Dishka provider `ZaloProvider` và các schema, webhook liên kết Zalo vẫn giữ nguyên 100%. Không xóa bất kỳ dòng code nào.

### Rationale
- Đạt được chính xác yêu cầu của người dùng: Zalo Bot hoàn toàn không phát sinh tin nhắn thông báo làm phiền nữa.
- Codebase an toàn tuyệt đối, không có rủi ro gãy dependency injection (Dishka) hay lỗi import.
- Khi tổ chức cần mở lại thông báo Zalo trong tương lai, chỉ cần đặt `ENABLE_ZALO_NOTIFICATION=true` trong file `.env` mà không phải code lại.

### Giải pháp thay thế đã xem xét (Alternatives Considered)
- *Xóa `zalo_channel.py`*: Vi phạm trực tiếp chỉ đạo của người dùng ("chứ đừng xóa code nhé").
- *Xóa `user.zalo_bot_id` trong DB*: Gây mất mát dữ liệu liên kết tài khoản của người dùng.

---

## 3. Nghiên cứu & Quyết định 3: Tác động đến 4 Scanners trong Reminder Engine

### Vấn đề (Context)
Hệ thống nhắc việc hiện có 4 Task Scanner độc lập:
1. `HomeworkTaskScanner`: Quét bài tập về nhà.
2. `DutyTaskScanner`: Quét lịch trực nhật vệ sinh hôm nay (hạn chót 22:00).
3. `MeetingEvaluationTaskScanner`: Quét đánh giá cuộc họp (hạn chót 72h sau kết thúc).
4. `UpcomingMeetingScanner`: Quét lịch họp sắp diễn ra.

Tất cả 4 scanner này đều gọi qua hàm trung gian `calculate_matching_stages(deadline, now)`.

### Quyết định (Decision)
- **Tập trung thay đổi tại Domain Entity**: Thay đổi hàm `ReminderStage.calculate_matching_stages(deadline, now)` trong `app.reminder.domain.entity.py`.
- Vì cả 4 scanners đều ủy quyền cho hàm này, việc cập nhật hàm domain sẽ tự động áp dụng chính sách đếm ngược 3 mốc (24h, 4h, 1h) đồng bộ cho toàn bộ 4 scanners mà không cần can thiệp phức tạp vào từng scanner:
  - `DutyTaskScanner`: Ca trực nhật có hạn chót 22:00 cùng ngày -> Lúc 18:00 (cách 4h) sẽ nhận `OFFSET_4H`, lúc 21:00 (cách 1h) sẽ nhận `OFFSET_1H`. Khung giờ 08:00 hay 12:00 sẽ không còn tự động réo.
  - `HomeworkTaskScanner`: Bài tập hạn 23:59 ngày mai -> Đúng 24h trước hạn nhận `OFFSET_1D`, 4h trước hạn nhận `OFFSET_4H`, 1h trước hạn nhận `OFFSET_1H`.
  - `UpcomingMeetingScanner`: Cuộc họp ngày mai -> Nhận `OFFSET_1D`, `OFFSET_4H`, `OFFSET_1H`.
  - `MeetingEvaluationTaskScanner`: Đánh giá 72h -> Nhận `OFFSET_1D`, `OFFSET_4H`, `OFFSET_1H`.

### Rationale
- Tuân thủ nghiêm ngặt Hiến pháp Principle I (Practical DDD): Logic tính toán mốc thời gian nằm trọn vẹn trong Domain Entity `ReminderStage`, tầng Application/Scanners chỉ việc tái sử dụng.
- Dễ dàng kiểm thử đơn vị (Unit Test) độc lập không cần database hay network.
