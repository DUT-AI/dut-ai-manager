# Phase 0: Research & Decision Log

## Decision: Loại bỏ toàn bộ ký tự Markdown trong Notification Messages
- **Vấn đề**: Các message notification khi gửi đa kênh (Multi-Channel Dispatcher) qua Zalo Bot, In-App Modal, Web Push bị lộ các ký tự Markdown (`**`, `*`, `` ` ``, `[]()`) vì chỉ có Discord Embed mới render Markdown một phần. Zalo Bot và In-App Web Text chỉ hiển thị text thuần hoặc hỗ trợ rất hạn chế, gây rối mắt cho người dùng.
- **Giải pháp**:
  - Chuẩn hóa text nội dung thông báo thành plain text trực quan, dùng ngắt dòng `\n`, emoji đại diện trực quan (`📢`, `⏰`, `👤`, `📅`, `👉`, `•`, `⚠️`) và chữ in HOA cho các tiêu đề/phân mục chính.
  - Loại bỏ các ký tự sao `**bold**` $\rightarrow$ giữ nguyên từ khóa hoặc viết hoa nhẹ nếu là tiêu đề.
  - Thay thế link markdown `[Nhấn vào đây](url)` $\rightarrow$ URL trực tiếp hoặc để nút/dòng `👉 Xem chi tiết tại: {url}`.
  - Sửa `ZaloNotificationChannel`: Không bọc `*{payload.title}*` bằng dấu sao, hiển thị `📢 {payload.title}`.
- **Alternatives Considered**:
  - *Viết bộ hàm parse/strip Markdown tại từng channel adapter*: Phức tạp, dễ sót trường hợp, làm tăng chi phí runtime và có thể cắt xén sai URL.
  - *Chuẩn hóa ngay tại nguồn tạo NotificationPayload*: Đảm bảo tính nhất quán (Single Source of Truth), dữ liệu lưu trong In-App DB sạch sẽ, hiển thị đẹp trên mọi kênh (Zalo, Discord, Web Push, In-App).
