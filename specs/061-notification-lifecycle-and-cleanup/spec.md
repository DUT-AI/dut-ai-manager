# Feature Specification: Notification Lifecycle, User-driven Delete, and TTL Housekeeping

- **Feature Directory**: `specs/061-notification-lifecycle-and-cleanup`
- **Created Date**: 2026-11-11
- **Status**: Draft
- **Target Release**: Backend & Frontend Notification System

---

## 1. Executive Summary & Problem Statement

### 1.1 Context & Problem
Hiện tại hệ thống thông báo (`notifications`) đã chuyển hoàn toàn sang cơ chế **Hard Delete** (không còn cột `is_deleted`). Bảng `notifications` không chỉ phục vụ hiển thị trên giao diện (Web/PWA/Zalo) mà còn lưu trữ metadata kỹ thuật (`task_type`, `task_id`, `reminder_stage`, `created_at`) để Reminder Engine thực hiện **Deduplication** (chống bắn trùng) và **Cooldown** (chống spam thông báo).

Nếu người dùng bấm đọc mà xóa ngay lập tức (Hard Delete), Reminder Scanner trong lần quét tiếp theo sẽ thấy bản ghi không còn trong DB và tiếp tục bắn lại tin nhắn nhắc việc qua Discord/Zalo/Web Push, gây spam nghiêm trọng cho người dùng và làm hỏng trải nghiệm người dùng khi muốn xem lại nội dung/link họp cũ.

Đồng thời:
1. Người dùng hiện **chưa có tính năng xóa chủ động** (Xóa 1 thông báo cụ thể hoặc Xóa toàn bộ thông báo đã đọc) để dọn sạch thanh thông báo cá nhân.
2. Dữ liệu thông báo trong Database tích lũy theo thời gian dài sẽ phình to nếu không có cơ chế **tự động dọn dẹp (TTL / Housekeeping Job)**.

---

## 2. Goals & Non-Goals

### 2.1 Goals
- **User-driven Deletion**: Cung cấp API và tương tác cho người dùng:
  - Xóa 1 thông báo cá nhân (`DELETE /api/v1/notifications/{id}`).
  - Xóa tất cả các thông báo đã đọc của cá nhân (`DELETE /api/v1/notifications/read-all`).
- **TTL Housekeeping Job**: Thiết lập cơ chế định kỳ (hàng ngày / hàng tuần hoặc qua cron) tự động xóa vĩnh viễn các thông báo đã đọc quá hạn (mặc định > 30 ngày) để tối ưu dung lượng DB.
- **Bảo vệ Reminder Engine**:
  - Tách bạch rõ ràng giữa hành động "Đọc" (`mark_as_read` - giữ nguyên thông báo để chống duplicate reminder) và "Xóa" (xóa chủ động hoặc dọn dẹp sau 30 ngày khi đã hết hạn task).
  - Đảm bảo các scanner nhắc việc hoạt động ổn định, chính xác.

### 2.2 Non-Goals
- Không áp dụng xóa mềm (`is_deleted`) trở lại cho bảng `notifications` (giữ nguyên chuẩn Hard Delete đã migrate).
- Không tự động xóa các thông báo **chưa đọc** (`is_read = false`) trong Housekeeping Job trừ khi đã quá hạn rất dài (ví dụ > 90 ngày) để tránh làm mất thông báo quan trọng của người dùng.

---

## 3. User Stories & Scenarios

### User Story 1: Người dùng đánh dấu đã đọc (Mark as Read)
Là một người dùng hệ thống:
- Khi tôi click vào một thông báo chưa đọc, hệ thống chỉ cập nhật trạng thái `is_read = True` và ghi nhận `read_at = NOW()`.
- Thông báo vẫn xuất hiện trong danh sách thông báo để tôi có thể xem lại chi tiết/link, đồng thời số lượng badge chưa đọc giảm đi.

### User Story 2: Người dùng xóa chủ động (User-driven Delete)
Là một người dùng hệ thống:
- Khi tôi không còn muốn thấy một thông báo nào đó trong khay thông báo, tôi có thể bấm nút "Xóa" cạnh thông báo đó (`DELETE /api/v1/notifications/{id}`).
- Khi tôi muốn dọn nhanh hộp thư thông báo, tôi có thể bấm nút "Xóa tất cả đã đọc" (`DELETE /api/v1/notifications/read-all`).
- Hệ thống chỉ cho phép người dùng xóa các thông báo thuộc về chính họ (RBAC / Ownership validation).

### User Story 3: Hệ thống tự động dọn dẹp thông báo cũ (Automated Housekeeping / TTL)
Là một quản trị viên / kỹ sư vận hành:
- Hệ thống có tác vụ chạy nền định kỳ (ví dụ mỗi đêm hoặc hàng tuần) tự động dọn sạch các bản ghi thông báo đã đọc (`is_read = True`) được tạo trước đó hơn 30 ngày (`created_at < NOW() - 30 days`).
- Tác vụ trả về số lượng bản ghi đã được dọn dẹp và log lại thông tin audit.

---

## 4. Technical Requirements & Architecture

### 4.1 Backend APIs
1. **`DELETE /api/v1/notifications/{id}`**:
   - Yêu cầu xác thực: Bearer Token của người dùng.
   - Logic: Kiểm tra `notification.user_id == current_user.id`. Nếu không tìm thấy hoặc không thuộc user thì trả về 404/403. Nếu hợp lệ, gọi `repo.hard_delete(id)`.
   - Response: `ApiResponse[bool]`.
2. **`DELETE /api/v1/notifications/read-all`**:
   - Yêu cầu xác thực: Bearer Token của người dùng.
   - Logic: Thực hiện xóa hàng loạt các thông báo thỏa mãn `user_id == current_user.id AND is_read == True`.
   - Response: `ApiResponse[int]` (trả về số lượng bản ghi đã xóa).
3. **Housekeeping Service / Command**:
   - Class `CleanExpiredNotificationsUseCase` / Cron task:
     ```python
     def execute(self, retention_days: int = 30) -> int:
         cutoff_date = datetime.now(UTC) - timedelta(days=retention_days)
         return self.notification_repo.delete_read_before(cutoff_date)
     ```
   - Tích hợp vào hệ thống scheduler / coordinator hiện có của ứng dụng (trong `app/reminder/application/scheduler_coordinator.py`).

### 4.2 Frontend (UI/UX)
- Cập nhật service `notification.service.ts` để gọi API xóa 1 thông báo và xóa tất cả đã đọc.
- Bổ sung nút "Xóa" trên item thông báo và nút "Dọn dẹp thông báo đã đọc" trên menu thông báo.

---

## 5. Acceptance Criteria

1. Khi gọi `PATCH /api/v1/notifications/{id}/read`, thông báo được cập nhật `is_read = True`, **không bị xóa khỏi DB**.
2. Khi gọi `DELETE /api/v1/notifications/{id}`, chỉ xóa đúng thông báo của user đó khỏi DB; user khác không thể xóa thông báo của người khác.
3. Khi gọi `DELETE /api/v1/notifications/read-all`, chỉ các thông báo đã đọc (`is_read = true`) của user hiện tại bị xóa, thông báo chưa đọc vẫn giữ nguyên.
4. Housekeeping Job khi chạy với `retention_days = 30` xóa đúng các thông báo đã đọc cũ hơn 30 ngày và không xóa các thông báo mới tạo hoặc chưa đọc.
5. Unit tests và API tests được viết đầy đủ và đạt 100% passed.
