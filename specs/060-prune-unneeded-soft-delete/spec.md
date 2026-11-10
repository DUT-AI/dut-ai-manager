# Feature Specification: Lược bỏ is_deleted trên các Model không cần thiết (Prune Unneeded Soft Delete)

**Feature Branch**: `060-prune-unneeded-soft-delete`

**Created**: 2026-11-11

**Status**: Draft

**Input**: User request: "Hãy xem thử các model sẵn có, cái nào nên bỏ is_deleted?"

---

## 1. Khảo sát thực tế Dữ liệu trên Cơ sở dữ liệu Production

Dữ liệu khảo sát từ môi trường Production (`dut_ai_manager_prod`) ngày 11/11/2026:

| Bảng Cơ sở dữ liệu | Tổng số bản ghi | Đã xóa (`is_deleted=true`) | Đánh giá nghiệp vụ | Đề xuất |
| :--- | :---: | :---: | :--- | :--- |
| `notifications` | 3,375 | **0** | Thông báo hệ thống/người dùng. Đã có cờ `is_read`. Xóa là hard delete. | **BỎ `is_deleted`** |
| `push_subscriptions` | 67 | **0** | Token Web Push VAPID theo thiết bị. Đã có cờ `is_active`. Xóa/hết hạn là hard delete. | **BỎ `is_deleted`** |
| `homework_assignees` | 757 | **0** | Bảng phân công bài tập (Junction Table giữa Homework và User). Cascade delete. | **BỎ `is_deleted`** |
| `invoice_items` | 498 | **0** | Chi tiết từng dòng của hóa đơn (Child items). Phụ thuộc vòng đời của Invoice cha. | **BỎ `is_deleted`** |
| `monthly_user_stats` | 235 | **0** | Bảng số liệu thống kê/snapshot định kỳ (Aggregate read model). Tính toán lại thì overwrite/delete. | **BỎ `is_deleted`** |
| `user_roles` | 117 | **0** | Bảng liên kết N-N giữa User và Role. Thu hồi quyền là xóa vĩnh viễn dòng quan hệ. | **BỎ `is_deleted`** |
| `cleaning_duties` | 2 | **0** | Lịch trực nhật tuần. Thường chỉ cập nhật status (PENDING/APPROVED/REJECTED). | **BỎ `is_deleted`** |
| `meeting_evaluations` | 551 | **0** | Điểm đánh giá buổi học (Feedback/Score item). | **BỎ `is_deleted`** |
| `meeting_overall_evaluations` | 20 | **0** | Đánh giá tổng thể buổi học (1-1 với Meeting). Đi kèm vòng đời của Meeting. | **BỎ `is_deleted`** |
| `permissions` | 58 | **0** | Danh mục quyền tĩnh hệ thống (Static Seeded RBAC Catalog). Không ai soft-delete quyền tĩnh. | **BỎ `is_deleted`** |
| `roles` | 13 | **0** | Danh mục vai trò tĩnh hệ thống (Admin, Mentor, Trainee...). Không soft-delete. | **BỎ `is_deleted`** |
| `teams` | 9 | **0** | Danh mục Team/Nhóm. Số lượng ít, không xóa mềm. | **BỎ `is_deleted`** |
| `accounts` | 91 | **0** | Tài khoản ngân hàng/quỹ. Đã có trạng thái active. | Xem xét giữ hoặc bỏ |
| `meeting_participants` | 2,565 | **64** | Điểm danh/tham gia buổi học. Xóa người tham gia là hard delete. | **BỎ `is_deleted` (Theo yêu cầu User)** |
| `meetings` | 168 | **44** | Buổi sinh hoạt. Xóa buổi sinh hoạt là hard delete (cascade evaluations & participants). | **BỎ `is_deleted` (Theo yêu cầu User)** |
| `homeworks` | 51 | **8** | Đề bài tập. Xóa bài tập là hard delete (cascade assignees & submissions). | **BỎ `is_deleted` (Theo yêu cầu User)** |
| `violations` | 1,227 | **853** | Vi phạm kỷ luật. Bắt buộc giữ lịch sử để tra cứu khi khiếu nại. | **GIỮ `is_deleted`** |
| `permission_requests` | 746 | **34** | Đơn xin phép (vắng, trễ, đổi ca). Cần lưu vết đơn đã thu hồi/hủy. | **GIỮ `is_deleted`** |
| `invoices` | 346 | **20** | Hóa đơn tài chính/thu quỹ. Bắt buộc lưu vết kiểm toán kế toán. | **GIỮ `is_deleted`** |
| `team_members` | 256 | **19** | Thành viên nhóm (lịch sử tham gia/rời nhóm). | **GIỮ `is_deleted`** |
| `outgoing_invoices` | 55 | **2** | Hóa đơn chi. Bắt buộc kiểm toán tài chính. | **GIỮ `is_deleted`** |
| `users` | 90 | **2** | Tài khoản thành viên. Khóa/vô hiệu hóa tài khoản. | **GIỮ `is_deleted`** |
| `bonus_points` | 290 | **1** | Điểm thưởng cộng/trừ. | **GIỮ `is_deleted`** |
| `role_api_keys` | 10 | **1** | API Keys. Thu hồi key. | **GIỮ `is_deleted`** |
| `role_permissions` | 142 | **1** | Cấu hình phân quyền động. | **GIỮ `is_deleted`** |

---

## 2. Tiêu chí Quyết định (Domain-Driven Design Guidelines)

### Nhóm 1: BỎ `is_deleted` (Chuyển sang Hard Delete)
1. **Meetings & Meeting Participants (`meetings`, `meeting_participants`)**:
   - Nghiệp vụ: Khi Admin hoặc Trainer xóa một buổi học hoặc xóa người tham dự, hệ thống xóa vật lý (Hard Delete) cùng cascade các dữ liệu con.
   - Vấn đề: Soft delete gây duplicate meeting hoặc vướng lịch trùng nhau khi tạo lại buổi sinh hoạt cùng khung giờ.
2. **Homeworks (`homeworks`, `homework_assignees`)**:
   - Nghiệp vụ: Khi xóa bài tập, cascade xóa phân công và bài nộp theo dạng dọn dẹp sạch sẽ.
3. **Bảng liên kết N-N / Junction Tables (`user_roles`, `homework_assignees`)**:
   - Nghiệp vụ: Gán và thu hồi quyền/bài tập. Xóa cứng tránh xung đột unique key khi gán lại.
4. **Bảng dữ liệu sự kiện / Thông báo / Tạm thời (`notifications`, `push_subscriptions`)**:
   - Nghiệp vụ: Thông báo và token thiết bị chỉ có giá trị thời điểm, đã có `is_read` và `is_active`.
5. **Bảng chi tiết con phụ thuộc (`invoice_items`)**:
   - Nghiệp vụ: Chi tiết hóa đơn đi theo vòng đời hóa đơn cha.
6. **Bảng cấu hình tĩnh / Seeded Catalog (`permissions`, `roles`, `teams`)**:
   - Dữ liệu cấu hình hệ thống cố định.
7. **Bảng thống kê định kỳ / Snapshot Aggregate (`monthly_user_stats`)**:
   - Snapshot tổng hợp số liệu, tính lại thì overwrite/delete.

### Nhóm 2: BẮT BUỘC GIỮ `is_deleted` (Opt-in Soft Delete)
1. **Dữ liệu tài chính, kế toán, pháp lý (`invoices`, `outgoing_invoices`)**: Luật kế toán và kiểm toán không cho phép xóa vĩnh viễn chứng từ thu/chi.
2. **Dữ liệu vi phạm, kỷ luật (`violations`, `permission_requests`)**: Cần bằng chứng lịch sử khi sinh viên khiếu nại hoặc đối soát điểm rèn luyện.
3. **Tài khoản người dùng (`users`)**: Vô hiệu hóa/khóa tài khoản (deactivation) để bảo toàn toàn vẹn dữ liệu.

---

## 3. User Scenarios & Testing *(mandatory)*

### User Story 1 - Chuyển đổi các bảng Junction & Config tĩnh sang Hard Delete (Priority: P1) 🎯 MVP
Là một nhà phát triển backend, tôi muốn các bảng trung gian như `user_roles`, `homework_assignees` và bảng cấu hình như `permissions`, `roles` sử dụng `SQLAlchemyTimestampOnlyMixin` hoặc `SQLAlchemyAuditMixin` thay vì `SQLAlchemyTimestampMixin` (có `is_deleted`), để khi xóa bản ghi thì thực hiện hard delete trực tiếp mà không cần check cờ xóa mềm.

**Independent Test**:
- Kiểm thử thu hồi role từ user: Gọi hàm xóa quyền, kiểm tra bản ghi trong bảng `user_roles` bị xóa vật lý khỏi database. Khi gán lại role đó cho user, không xảy ra xung đột bản ghi cũ.

### User Story 2 - Tối ưu hóa bảng Thông báo và Push Subscription (Priority: P2)
Là một kỹ sư vận hành hệ thống, tôi muốn bảng `notifications` và `push_subscriptions` không còn cột `is_deleted`, giúp giảm tải dung lượng lưu trữ và tối ưu tốc độ truy vấn danh sách thông báo.

**Independent Test**:
- Kiểm thử xóa thông báo: Gọi API xóa thông báo, bản ghi bị xóa hoàn toàn khỏi DB. Câu lệnh query thông báo chưa đọc không còn phải `WHERE is_deleted = false`.

### User Story 3 - Viết Migration Alembic dọn dẹp cột an toàn (Priority: P3)
Là một kỹ sư DevOps, tôi muốn có migration script Alembic chuẩn để `DROP COLUMN is_deleted` trên các bảng thuộc diện loại bỏ, đảm bảo không ảnh hưởng đến dữ liệu đang chạy của các bảng được giữ lại.

---

## 4. Kế hoạch Thực hiện theo Giai đoạn (Phased Rollout)

- **Giai đoạn 1 (Nguy cơ rủi ro = 0, khuyến nghị làm ngay)**:
  - `user_roles`: Chuyển sang hard delete.
  - `notifications`: Chuyển sang hard delete.
  - `push_subscriptions`: Chuyển sang hard delete.
  - `permissions` & `roles`: Bỏ `is_deleted`.
  - `monthly_user_stats`: Bỏ `is_deleted`.
  - `homework_assignees`: Bỏ `is_deleted`.
- **Giai đoạn 2 (Đánh giá thêm)**:
  - `cleaning_duties`, `invoice_items`, `meeting_evaluations`, `meeting_overall_evaluations`.
