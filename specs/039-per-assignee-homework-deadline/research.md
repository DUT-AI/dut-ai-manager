# Phase 0: Research & Technical Decisions (039-per-assignee-homework-deadline)

## Bối cảnh & Yêu cầu từ Người dùng
- **Quyết định dứt khoát**: Xóa bỏ hoàn toàn trường `deadline` trên bảng `homeworks`, chuyển hẳn sang lưu trữ trong bảng `homework_assignees`.
- Điều này tuân thủ nguyên tắc **Constitution Rule X: Zero Redundant Backward Compatibility & No Duplicate Columns**. Không duy trì song song 2 cột deadline gây nhầm lẫn hoặc lệch dữ liệu (single source of truth).

---

## Các Quyết định Kỹ thuật (Decisions & Rationale)

### 1. Schema Migration: Di chuyển cột `deadline`
- **Quyết định**:
  1. Thêm cột `deadline TIMESTAMPTZ NULL` vào bảng `homework_assignees`.
  2. Backfill: Cập nhật `ha.deadline = h.deadline` cho tất cả bản ghi hiện có từ bảng `homeworks`.
  3. Cập nhật thêm cho các đơn `POSTPONE` hợp lệ đang có hiệu lực: `ha.deadline = pr.start_time`.
  4. Đổi `ha.deadline` thành `NOT NULL` và đánh Index (`ix_homework_assignees_deadline`).
  5. Xóa cột `deadline` khỏi bảng `homeworks` (`ALTER TABLE homeworks DROP COLUMN deadline`).
- **Lý do**: Đảm bảo toàn vẹn dữ liệu, không làm mất bất kỳ deadline nào của các bài tập cũ, đồng thời loại bỏ hoàn toàn cột thừa trên `homeworks`.

---

### 2. Quản lý Vòng đời Đơn xin hoãn (`POSTPONE`) mà không cần `homework.deadline`
- **Vấn đề**: Khi không còn `homework.deadline`, làm sao để:
  1. Kiểm tra giới hạn gia hạn không vượt quá 4 ngày?
  2. Hoàn nguyên hạn nộp cũ khi người dùng xoá/huỷ đơn xin hoãn?
- **Quyết định**:
  1. Khi học viên tạo đơn `POSTPONE`:
     - Lấy deadline hiện tại của học viên: `current_deadline = homework_assignee_repo.get_user_deadline(homework_id, user_id)`.
     - Kiểm tra: `new_deadline > current_deadline` và `(new_deadline - current_deadline).total_seconds() <= 4 * 24 * 3600`.
  2. Bổ sung trường `old_deadline: datetime | None` vào `PostponePayload`:
     - Khi lưu đơn, ghi nhận `payload.old_deadline = current_deadline`.
  3. Khi đơn bị xoá (`on_deleted`):
     - Nếu có `payload.old_deadline`: hoàn nguyên `homework_assignee_repo.update_deadline(homework_id, user_id, payload.old_deadline)`.
- **Lý do**: Đây là cơ chế State Snapshot cực kỳ sạch sẽ, lưu giữ vết biến động thời gian trực tiếp trong payload của đơn xin phép, độc lập hoàn toàn với bài tập gốc.

---

### 3. Tái cấu trúc Use Case Quét Vi phạm (`CheckOverdueHomeworkUseCase`)
- **Quyết định**:
  - `CheckOverdueHomeworkUseCase` không còn gọi `self.homework_repo.get_by_deadline_date()`.
  - Thay vào đó, gọi `self.homework_assignee_repo.get_by_deadline_date(target_date)`.
  - Hàm này join `homework_assignees` với `homeworks` (để lấy title, requirements) và lọc `date(homework_assignees.deadline AT TIME ZONE 'Asia/Ho_Chi_Minh') == target_date`.
  - Mỗi bản ghi trả về đại diện cho đúng 1 học viên đến hạn nộp bài.
  - Kiểm tra nộp bài trong DB: `submitted_at <= assignment.deadline`.
- **Lý do**:
  - Chạy nhanh hơn vì quét trúng đích từng học viên có hạn nộp vào ngày đó.
  - Giải quyết triệt để vấn đề: Học viên xin hoãn sẽ được quét đúng vào ngày deadline đã gia hạn (+ 2 ngày delay).

---

### 4. Xử lý API Read Model & Frontend Compatibility
- **API Admin (`/homeworks`)**:
  - Khi lấy danh sách bài tập ở trang quản lý, mỗi bài tập trả về `min_deadline` và `max_deadline` hoặc deadline đại diện để Admin quan sát (hoặc danh sách assignee kèm deadline).
- **API Học viên (`/my-homeworks`, `/homeworks/{id}`)**:
  - Trả về `deadline: assignee.deadline` của học viên đang đăng nhập.
  - Phía Frontend không cần đổi tên trường `deadline`, không bị vỡ UI.
