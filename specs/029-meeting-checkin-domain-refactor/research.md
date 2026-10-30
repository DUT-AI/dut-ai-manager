# Research: Meeting Check-In State Transition & Domain Rules

## 1. Participant Status Enum Analysis
Các trạng thái hiện có trong `app.meeting.domain.value_objects.ParticipantStatus`:
- `NOT_JOINED`: Trạng thái ban đầu khi thêm vào meeting. Chưa điểm danh.
- `JOINED`: Đã check-in thành công đúng giờ.
- `LATE_EXCUSED`: Đi trễ có phép (đã có đơn xin đi trễ được duyệt trước/trong buổi họp).
- `LATE_UNEXCUSED`: Đi trễ không phép (đến sau `meeting.start_time` mà không có đơn).
- `ABSENT_EXCUSED`: Vắng mặt có phép (đã có đơn xin vắng được duyệt).
- `ABSENT_UNEXCUSED`: Vắng mặt không phép (hết buổi họp vẫn chưa check-in).
- `COMPLETED`: Đã hoàn thành buổi họp (đã check-out hoặc được hệ thống auto-checkout lúc 23:59).

## 2. Check-In State Transition Matrix

| Trạng thái hiện tại | Thời điểm check-in | Trạng thái MỚI | `check_in_at` | `link_image` | Ghi chú nghiệp vụ |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `NOT_JOINED` | $\le \text{start\_time}$ | `JOINED` | Gán `check_in_time` | Gán `image_url` | Đúng giờ tiêu chuẩn |
| `NOT_JOINED` | $> \text{start\_time}$ | `LATE_UNEXCUSED` | Gán `check_in_time` | Gán `image_url` | Đi trễ không phép |
| `LATE_EXCUSED` | Bất kỳ lúc nào | `LATE_EXCUSED` (giữ nguyên) | Gán `check_in_time` | Gán `image_url` | Đã xin phép trước, khi có mặt ghi nhận giờ & ảnh nhưng bảo lưu quyền có phép |
| `JOINED` | Bất kỳ lúc nào | `JOINED` | Giữ nguyên (hoặc cập nhật nếu chưa có) | Cập nhật `image_url` nếu có ảnh mới | Bổ sung ảnh điểm danh hoặc check-in lại |
| `LATE_UNEXCUSED` | Bất kỳ lúc nào | `LATE_UNEXCUSED` | Giữ nguyên | Cập nhật `image_url` | Đã ghi nhận trễ, cho phép chụp lại ảnh |
| `ABSENT_EXCUSED` | Bất kỳ lúc nào | Nếu học viên xin vắng nhưng bất ngờ đến dự: chuyển sang `JOINED` hoặc `LATE_EXCUSED` | Gán `check_in_time` | Gán `image_url` | Đi học bất ngờ (dù đã xin vắng) |
| `COMPLETED` | Bất kỳ lúc nào | Bị từ chối (`success=False`) | Không đổi | Không đổi | Buổi họp đã kết thúc / đã checkout |

## 3. Idempotency & Time Window Analysis
- **Idempotency**: Nếu client gửi `client_event_id` trùng với `participant.client_event_id`, Use Case coi đây là yêu cầu mạng gửi lại (network retry) và trả về thành công mà không trigger lại domain events dư thừa.
- **Time Window**: Thiết bị quét thẻ/camera có thể hoạt động offline hoặc mạng chập chờn. Khi sync dữ liệu lên server, thiết bị gửi kèm `client_time`. Vì vậy, khung tìm kiếm buổi họp phải căn cứ vào `check_in_dt` thay vì `now` của server:
  - `window_start = check_in_dt - 30 minutes`
  - `window_end = check_in_dt + 30 minutes`
