# Feature Specification: Bắt buộc chọn ca hiện tại và kiểm tra có mặt khi xin đổi buổi meeting

**Feature Branch**: `058-require-current-meeting-for-change`

**Created**: 2026-11-10

**Status**: Draft

**Input**: User description: "Khi xem phép đổi buổi meeting tôi mong muốn user bắt buộc phải chọn ca hiện tại, và ca hiện tại phải có mặt user mới được đổi, nếu ko có mặt thì raise Lỗi về người dùng"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bắt buộc chọn ca hiện tại và kiểm tra sự hiện diện của User khi tạo đơn đổi ca (Priority: P1) 🎯 MVP

Là một học viên (Trainee/User), khi tôi tạo đơn xin phép đổi buổi meeting (`CHANGE_MEETING`), hệ thống:
1. **Bắt buộc** tôi phải chọn "Buổi sinh hoạt hiện tại" (`old_meeting_id`), không còn cho phép để trống (không chấp nhận giá trị `null`, `undefined` hay "Đăng ký mới").
2. **Kiểm tra sự có mặt (Attendance/Participant Verification)**: Kiểm tra xem tôi có thực sự là người tham gia (active participant, `is_deleted = false`) trong buổi sinh hoạt hiện tại đó hay không.
3. **Báo lỗi rõ ràng**: Nếu tôi không có tên trong danh sách tham gia của ca hiện tại, hệ thống lập tức từ chối và hiển thị thông báo lỗi: *"Bạn không có mặt trong danh sách tham gia của buổi sinh hoạt hiện tại đã chọn"*.

**Why this priority**: Ngăn chặn tình trạng học viên "đổi khống" từ một ca mà mình không hề được phân công, tránh gian lận chuyển ca hoặc spam giữ chỗ ở các ca khác mà không thực sự nhường lại chỗ ngồi ở ca ban đầu.

**Independent Test**:
- User A (đang tham gia Meeting 1) tạo đơn đổi sang Meeting 2: Chọn ca hiện tại là Meeting 1 -> Tạo đơn thành công.
- User A tạo đơn đổi sang Meeting 2 nhưng chọn ca hiện tại là Meeting 3 (Meeting mà User A không tham gia): Hệ thống raise lỗi HTTP 400 *"Bạn không có mặt trong danh sách tham gia của buổi sinh hoạt hiện tại đã chọn"*.
- User A gửi payload thiếu `old_meeting_id`: Hệ thống chặn ngay từ validation (HTTP 422 hoặc 400: *"Vui lòng chọn buổi sinh hoạt hiện tại"*).

**Acceptance Scenarios**:
1. **Given** User A là thành viên của Meeting 1,
   **When** User A tạo đơn xin đổi ca và chọn `old_meeting_id = 1`, `meeting_id = 2`,
   **Then** hệ thống xác thực User A có mặt trong Meeting 1, Meeting 2 còn chỗ, và tạo đơn đổi ca thành công.
2. **Given** User A KHÔNG phải là thành viên của Meeting 1,
   **When** User A cố tình gửi đơn đổi ca với `old_meeting_id = 1`,
   **Then** Backend trả về lỗi `HTTP 400 Bad Request` với message: *"Bạn không có mặt trong danh sách tham gia của buổi sinh hoạt hiện tại đã chọn"*.
3. **Given** Giao diện Web Frontend (`PermissionFormModal.tsx`) và Zalo Mini App (`PermissionFormModal.tsx`),
   **When** User chọn loại đơn `CHANGE_MEETING`,
   **Then** trường "Buổi sinh hoạt hiện tại" là bắt buộc (có dấu `*`, rules `required: true`), không còn tùy chọn "để trống nếu đăng ký mới", và dropdown chỉ gợi ý/cho phép chọn các ca mà user thực sự tham gia (hoặc validate tức thì).

---

### User Story 2 - Tối ưu danh sách chọn ca hiện tại trên Frontend (Priority: P2)

Là một học viên, khi tôi mở form đổi ca trên Web và Zalo Mini App, trường chọn "Buổi sinh hoạt hiện tại" nên tự động lọc hoặc làm nổi bật những buổi sinh hoạt mà tôi đã có tên tham gia để tôi không chọn nhầm.

**Why this priority**: Nâng cao trải nghiệm người dùng (UX), tránh việc user chọn bừa rồi bị hệ thống báo lỗi.

**Independent Test**:
- Mở modal đổi ca, dropdown "Buổi sinh hoạt hiện tại" hiển thị danh sách buổi học mà user có tham gia (hoặc hiển thị rõ tag "Đang tham gia").
- Nếu chọn một buổi mà mình không tham gia (nếu danh sách hiển thị tất cả), form sẽ cảnh báo hoặc Backend phản hồi lỗi chính xác.

**Acceptance Scenarios**:
1. **Given** User A chỉ có lịch học ở Ca Thứ 3,
   **When** User A mở form đổi ca,
   **Then** dropdown ca hiện tại ưu tiên hiển thị Ca Thứ 3, và khi submit form gửi đúng `old_meeting_id`.

---

### Edge Cases

- **Học viên đã bị xóa (soft-delete / `is_deleted = true`) khỏi ca hiện tại**: Vẫn tính là không có mặt trong ca hiện tại $\rightarrow$ Raise lỗi không hợp lệ.
- **Ca hiện tại và ca đích giống nhau**: `old_meeting_id == meeting_id` $\rightarrow$ Đã có validation chặn: *"Không thể đổi sang cùng một buổi họp"*.
- **Ca hiện tại đã diễn ra trong quá khứ**: Cần kiểm tra xem ca hiện tại có được phép đổi nếu ca đó đã kết thúc hay không (thông thường chỉ đổi các ca sắp diễn ra).
- **Học viên vắng mặt có phép ở ca hiện tại**: Nếu học viên đã có đơn vắng ở ca hiện tại nhưng muốn đổi ca, việc chuyển ca vẫn hợp lệ vì học viên vẫn là participant của ca đó.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Backend MUST cập nhật DTO `ChangeMeetingPayload` đưa trường `old_meeting_id: int` thành trường bắt buộc (non-optional).
- **FR-002**: Backend Strategy `ChangeMeetingStrategy.validate(...)` MUST kiểm tra `old_meeting_id`:
  - `old_meeting_id` không được rỗng/None.
  - User tạo đơn (`user_id`) PHẢI tồn tại trong danh sách người tham gia (`participants`) của `old_meeting_id` với trạng thái chưa bị xóa (`is_deleted == False`).
  - Nếu user KHÔNG có mặt trong `old_meeting_id`, MUST raise `HTTPException(status_code=400, detail="Bạn không có mặt trong danh sách tham gia của buổi sinh hoạt hiện tại đã chọn")`.
- **FR-003**: Web Frontend (`PermissionFormModal.tsx`) MUST đặt `rules: [{ required: true, message: 'Vui lòng chọn buổi sinh hoạt hiện tại!' }]` cho trường `old_meeting_id`. Xóa bỏ nhãn "để trống nếu đăng ký mới".
- **FR-004**: Zalo Mini App (`PermissionFormModal.tsx`) MUST đặt validation bắt buộc cho `formOldMeetingId` khi `formCategory === CHANGE_MEETING`.
- **FR-005**: Thông báo lỗi từ Backend trả về khi vi phạm phải hiển thị rõ ràng và thân thiện trên Toast/Notification của cả Web và Zalo Mini App.

### Key Entities

- **PermissionRequest[ChangeMeetingPayload]**: Đơn đổi buổi sinh hoạt chứa:
  - `old_meeting_id: int` (Bắt buộc - Ca hiện tại).
  - `meeting_id: int` (Bắt buộc - Ca đích chuyển đến).
  - `category: RequestCategory.CHANGE_MEETING`.
- **MeetingParticipant**: Bản ghi liên kết người tham gia với buổi họp (`user_id`, `meeting_id`, `is_deleted`).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% các request tạo đơn `CHANGE_MEETING` thiếu `old_meeting_id` hoặc có user không thuộc `old_meeting_id` bị từ chối với mã lỗi 400/422.
- **SC-002**: Đảm bảo toàn bộ test case kiểm thử đổi ca họp (`test_change_meeting...`) được cập nhật và pass 100%.
- **SC-003**: Frontend Web và Zalo Mini App không còn tồn tại hướng dẫn hoặc placeholder "để trống nếu đăng ký mới".
- **SC-004**: `npx tsc -b` trên Frontend và `pytest` trên Backend chạy thành công không có lỗi.

---

## Assumptions

- Tính năng đổi ca là hành động "chuyển giao vị trí" giữa 2 ca học: Người đổi phải đang giữ 1 chỗ ở Ca A để nhường lại chỗ đó cho người khác khi chuyển sang Ca B.
- Khái niệm "đăng ký mới vào một ca mà trước đó chưa có ca nào" không thuộc nghiệp vụ đổi ca (đó là việc phân công của Admin/Trainer).
