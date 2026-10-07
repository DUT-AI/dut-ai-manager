# Research: Đơn Xin Đổi Buổi Sinh Hoạt / Meeting (`CHANGE_MEETING`)

**Branch**: `007-change-meeting-permission-request` | **Date**: 2026-10-07

## 1. Technical Context & Domain Overview

- **Backend**: Python 3.11+ / FastAPI / SQLAlchemy 2.0 / Dishka IoC / EventBus / PostgreSQL / Pydantic v2.
- **Frontend / Mini App**: React / Vite / TypeScript / Tailwind CSS / Ant Design / Zalo Mini App SDK.
- **Timezone**: UTC+7 (`app.utils.datetime.get_current_utc7_time()`).
- **Core Entities Involved**: `PermissionRequest`, `Meeting`, `MeetingParticipant`, `User`.

---

## 2. Research Decisions & Architectural Trade-offs

### Decision 1: Available Seat Calculation & Concurrency Protection

- **Context**: Khi nhiều thành viên cùng lúc nộp đơn đổi sang Meeting B khi chỉ còn ít ghế trống (hoặc đúng 1 ghế), hệ thống phải tính chính xác và không được vượt quá `settings.MAX_SEATS` (mặc định 35).
- **Decision**: 
  - Công thức tính:
    $$\text{Occupied Seats} = \text{Count}(\text{MeetingParticipant active}) - \text{Count}(\text{Participant có đơn ABSENCE hợp lệ})$$
    $$\text{Available Seats} = \text{MAX\_SEATS} - \text{Occupied Seats}$$
  - Cơ chế đồng thời (Concurrency Control): Sử dụng Pessimistic Locking (`with_for_update()`) trên bản ghi `Meeting` đích (hoặc transaction lock) trong lúc kiểm tra ghế trống và gán participant mới.
- **Rationale**: Đảm bảo tính nhất quán dữ liệu tuyệt đối (ACID), loại bỏ hoàn toàn race condition khi tranh chấp ghế cuối cùng.
- **Alternatives Considered**: 
  - *Optimistic Locking with Versioning*: Phức tạp hơn và dễ gây retry storm cho người dùng khi nhiều request đồng thời nảy sinh xung đột.
  - *In-memory Redis Counter*: Tiềm ẩn nguy cơ lệch dữ liệu so với database gốc nếu có lỗi mạng hoặc crash.

### Decision 2: Atomic Participant Transfer & Cascade Invalidation

- **Context**: Khi đổi từ Meeting A sang Meeting B thành công, các trạng thái liên quan phải được cập nhật đồng bộ trong 1 transaction.
- **Decision**: Một Use Case chuyên biệt `CreateChangeMeetingRequestUseCase` (hoặc mở rộng `CreatePermissionRequestUseCase`) điều phối:
  1. Kiểm tra thời gian: `now < meeting_b.start_time` (naive UTC+7).
  2. Khóa và tính toán ghế trống của Meeting B.
  3. Xóa / rút `user_id` khỏi `MeetingParticipant` của Meeting A (nếu `old_meeting_id` có giá trị).
  4. Thêm `user_id` vào `MeetingParticipant` của Meeting B với status `NOT_JOINED`.
  5. Hủy mềm (soft-delete / invalidate) các đơn `ABSENCE` và `LATE` hiện hữu của `user_id` tại Meeting A.
  6. Lưu bản ghi `PermissionRequest` với category `CHANGE_MEETING`, `meeting_id = B`, `old_meeting_id = A`.
  7. Publish Domain Event `MeetingParticipantTransferred` / `PermissionRequestCreated`.
- **Rationale**: Tuân thủ nguyên tắc All-or-Nothing, tránh tình trạng thành viên bị rơi vào trạng thái lơ lửng (đã rút khỏi A nhưng chưa vào được B hoặc ngược lại).

### Decision 3: Event-Driven Multi-Channel Notification

- **Context**: Thông báo kết quả đổi ca cho cá nhân thành viên và thông báo biến động danh sách cho Ban quản trị / Host của Meeting A & B.
- **Decision**: 
  - Tạo Domain Event `MeetingParticipantTransferred(request_id, user_id, old_meeting_id, new_meeting_id, timestamp)`.
  - Đăng ký `MeetingParticipantNotificationHandler` lắng nghe event này trên `EventBus`.
  - Handler sử dụng `NotificationService` để:
    1. Gửi tin nhắn xác nhận cho cá nhân User qua Zalo Bot / Discord DM.
    2. Gửi thông báo đến Room quản lý Discord / Zalo Group về biến động danh sách sĩ số của Meeting A (-1) và Meeting B (+1).
- **Rationale**: Tuân thủ Constitution Principle IV — tách biệt hoàn toàn I/O mạng gửi tin nhắn khỏi HTTP transaction response, giúp API phản hồi tức thì (<100ms).

### Decision 4: Schema Evolution & Alembic Migration

- **Context**: Cần lưu trữ thông tin buổi học cũ `old_meeting_id` và giá trị enum mới `CHANGE_MEETING`.
- **Decision**:
  - Entity `PermissionRequest`: thêm thuộc tính `old_meeting_id: int | None = None`.
  - Value Object `RequestCategory`: thêm `CHANGE_MEETING = "CHANGE_MEETING"`.
  - Database Table `permission_requests`: thêm cột `old_meeting_id INTEGER REFERENCES meetings(id) ON DELETE SET NULL`, đánh index `ix_permission_requests_old_meeting_id`.
  - Alembic Migration: Tạo file migration mới cập nhật cột và enum.

### Decision 5: Frontend & Zalo Mini App User Experience

- **Context**: Người dùng cần biết rõ buổi nào còn bao nhiêu ghế trống để chọn, không để người dùng chọn buổi đã hết chỗ rồi mới báo lỗi.
- **Decision**:
  - Bổ sung trường `available_seats` vào DTO trả về của danh sách Meeting sắp tới (`MeetingWithSeatsDto` hoặc `MeetingSummaryDto`).
  - Giao diện form nộp đơn khi chọn category `CHANGE_MEETING`:
    - Dropdown 1: "Buổi học hiện tại" (liệt kê các meeting user đang tham gia + tùy chọn "Chưa có buổi học nào").
    - Dropdown 2: "Buổi học muốn chuyển đến" (chỉ liệt kê các meeting trong tương lai `start_time > now`, hiển thị tag số ghế trống `[Còn X chỗ]`, vô hiệu hóa các buổi có $X = 0$).
- **Rationale**: Tối ưu trải nghiệm người dùng, giảm thiểu thao tác lỗi.

---

## 3. Summary of Decisions

| Vấn đề | Quyết định kỹ thuật | Lý do chính |
|---|---|---|
| Kiểm tra ghế trống | $\text{MAX\_SEATS} - (\text{Participants} - \text{Đơn ABSENCE})$ + Row Lock | Ngăn chặn race condition vượt quá sĩ số tối đa |
| Chuyển participant | DB Transaction nguyên tử (Rút khỏi A, Thêm vào B, Hủy đơn cũ) | Đảm bảo tính toàn vẹn dữ liệu, không tạo dữ liệu rác |
| Ràng buộc thời gian | `now < meeting_b.start_time` (UTC+7) | Cho phép đổi linh hoạt kể cả sau khi ca A đã kết thúc |
| Thông báo | Event-driven qua `EventBus` $\rightarrow$ `NotificationService` | Phản hồi API nhanh, không nghẽn transaction |
| Giao diện | Dropdown realtime hiển thị số ghế trống | Trực quan, ngăn người dùng chọn ca đã đầy |
