# Research & Technical Decisions: DB-First Submission Check

**Feature**: `013-fix-my-homeworks-coding-submitted` | **Date**: 2026-10-17

## 1. Khảo Sát & Phân Tích

- **Tác vụ đọc (Query)**: Trung bình một học viên mở trang My Homeworks từ 5-20 lần/ngày. Với cơ chế cũ, mỗi lần tải trang, backend phải gọi đồng thời 2 x N cuộc gọi HTTP sang Quiz API (N = số bài tập hiển thị trên trang). Điều này dẫn đến:
  - Nguy cơ cạn kiệt connection pool.
  - Phụ thuộc hoàn toàn vào uptime và tốc độ của máy chủ Quiz API.
  - Timeout 5s khiến người dùng đã nộp bài bị hiển thị nhầm thành "Chưa nộp".
- **Kiến trúc DB-First**:
  - Dữ liệu bài nộp được lưu trữ bền vững tại bảng `homework_submissions` thông qua Webhook hoặc các lần đồng bộ.
  - Khi xem danh sách bài tập, hệ thống chỉ cần JOIN / SELECT WHERE `user_id = :uid` trong bảng `homework_submissions`. Tốc độ query đạt < 10ms trên PostgreSQL có index.
  - Đảm bảo tính nhất quán (Consistency): Không còn tình trạng refresh lúc ra "Đã nộp", lúc ra "Chưa nộp".

## 2. Thiết Kế Nút Sync Cho Học Viên

- Học viên sau khi bấm nộp bài trên giao diện web của Quiz, có thể quay lại DUT AI Manager bấm **"Đồng bộ kết quả"**.
- Backend sẽ chỉ thực hiện sync bài tập cụ thể đó từ Quiz API và lưu vào bảng `homework_submissions`.
- Frontend ngay lập tức invalidate query `['homeworks', 'me']` để hiển thị kết quả vừa nộp.
