# Feature Specification: Đơn Xin Đổi Buổi Sinh Hoạt / Meeting (`CHANGE_MEETING`)

**Feature Branch**: `007-change-meeting-permission-request`

**Created**: 2026-10-06

**Status**: Draft

**Input**: User description: "Thêm chức năng xin đổi meeting trong permission request, cho phép đổi từ meeting A sang meeting B (hoặc đăng ký mới vào meeting B nếu chưa có meeting). Hệ thống tự động kiểm tra số lượng ghế còn lại = MAX_SEAT - (số người đăng ký - số người xin phép vắng). Tự động duyệt và chuyển participant nếu còn chỗ."

## Clarifications

### Session 2026-10-06
- Q: Cơ chế phê duyệt cho loại đơn xin đổi meeting sẽ hoạt động như thế nào? → A: Tự động duyệt ngay (Auto-Approve) nếu Meeting B còn ghế trống (`Ghế còn lại > 0`).
- Q: Cách thức xác định Meeting ban đầu (Meeting A) của người làm đơn sẽ diễn ra như thế nào? → A: Form hiển thị dropdown các buổi Meeting sắp tới mà user đang tham gia, kèm tùy chọn "Chưa có buổi học nào (Đăng ký mới)", cùng dropdown chọn Meeting đích (Meeting B).
- Q: Khi đổi thành công sang Meeting B, hệ thống xử lý các đơn xin phép cũ ở Meeting A như thế nào và thời hạn chót được đổi là khi nào? → A: Tự động xóa/hủy đơn vắng hoặc trễ liên quan đến Meeting A cũ; cho phép đổi tự do trước khi Meeting B bắt đầu.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Thành viên xin chuyển từ Meeting A sang Meeting B còn chỗ (Priority: P1)

Thành viên đang có tên trong danh sách tham gia của Meeting A (ví dụ ca sáng T7) nhưng bận đột xuất, muốn chuyển sang tham gia Meeting B (ví dụ ca chiều CN). Thành viên mở form xin phép, chọn loại đơn "Xin đổi buổi sinh hoạt", chọn Meeting A hiện tại và Meeting B mong muốn. Hệ thống kiểm tra Meeting B còn ghế trống, lập tức phê duyệt, rút thành viên khỏi Meeting A và ghi danh vào Meeting B.

**Why this priority**: Đây là luồng nghiệp vụ cốt lõi, giải quyết nhu cầu chuyển ca học/họp linh hoạt của thành viên mà không cần sự can thiệp thủ công từ quản trị viên.

**Independent Test**:
- Tạo 2 buổi họp A và B (B còn 5 chỗ).
- User 1 đang ở A, gửi đơn đổi sang B.
- Kết quả: User 1 không còn ở A (+1 ghế trống cho A), User 1 xuất hiện ở B (-1 ghế trống của B), đơn chuyển sang trạng thái đã xử lý thành công.

**Acceptance Scenarios**:
1. **Given** User đang tham gia Meeting A và Meeting B có ghế còn lại > 0, **When** User gửi đơn đổi sang Meeting B trước giờ bắt đầu của B, **Then** Đơn được chấp thuận ngay, User được chuyển sang Meeting B và rút khỏi Meeting A.
2. **Given** Meeting B đã đủ số người tham dự tối đa (ghế còn lại = 0), **When** User cố gắng gửi đơn đổi sang Meeting B, **Then** Hệ thống từ chối yêu cầu và hiển thị thông báo lỗi "Buổi họp đã hết chỗ ngồi".

---

### User Story 2 - Thành viên chưa có buổi học xin đăng ký vào Meeting B (Priority: P2)

Thành viên chưa được phân công hoặc chưa có tên trong buổi họp nào trong tuần, muốn xin đăng ký tham gia vào Meeting B. Thành viên chọn Meeting gốc là "Chưa có buổi học nào" và chọn Meeting B. Hệ thống kiểm tra chỗ ngồi và thêm thành viên vào Meeting B.

**Why this priority**: Cho phép học viên bổ sung hoặc học bù khi chưa có lịch từ trước.

**Independent Test**:
- User chưa ở trong meeting nào trong tuần.
- Gửi đơn xin vào Meeting B (còn chỗ).
- Kết quả: User được thêm làm participant của Meeting B.

**Acceptance Scenarios**:
1. **Given** User không thuộc Meeting nào và Meeting B còn chỗ, **When** User chọn "Chưa có buổi học nào" và gửi đơn xin vào B, **Then** Hệ thống thêm User vào Meeting B thành công.

---

### User Story 3 - Tự động dọn dẹp đơn xin vắng cũ khi chuyển ca thành công (Priority: P3)

Trước đó User đã gửi đơn xin vắng (`ABSENCE`) cho Meeting A vì nghĩ mình không tham gia được. Sau đó, User thấy Meeting B phù hợp và gửi đơn đổi sang B thành công. Hệ thống tự động thu hồi/hủy đơn xin vắng ở Meeting A để tránh rác dữ liệu và sai lệch thống kê.

**Why this priority**: Đảm bảo tính toàn vẹn và nhất quán của dữ liệu điểm danh và quét vi phạm.

**Independent Test**:
- User có đơn xin vắng tại Meeting A.
- Đổi ca sang Meeting B thành công.
- Kết quả: Đơn xin vắng tại Meeting A bị hủy / xóa bỏ.

**Acceptance Scenarios**:
1. **Given** User có đơn xin vắng đang hiệu lực tại Meeting A, **When** User đổi ca sang Meeting B thành công, **Then** Đơn xin vắng tại Meeting A được tự động hủy/xóa.

---

### Edge Cases

- **Meeting B đã bắt đầu hoặc đã kết thúc**: Hệ thống chặn không cho nộp đơn đổi sang Meeting B nếu thời điểm hiện tại `now >= meeting_b.start_time`.
- **Đổi sang chính Meeting đang ở ($A = B$)**: Hệ thống báo lỗi validation ngay tại frontend và backend ("Không thể đổi sang cùng một buổi họp").
- **Tranh chấp ghế cuối cùng (Race Condition)**: Khi Meeting B chỉ còn đúng 1 ghế và có 2 thành viên cùng gửi đơn đồng thời, cơ chế khóa giao dịch (Transaction Lock) đảm bảo chỉ 1 người thành công, người thứ hai nhận thông báo hết chỗ.
- **Tính toán ghế trống theo đơn vắng**: Một người ở Meeting B có đơn `ABSENCE` hợp lệ thì người đó không chiếm ghế, ghế đó được tính là ghế trống sẵn sàng cho người khác đổi vào.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống MUST bổ sung loại danh mục yêu cầu mới `CHANGE_MEETING` (Đổi buổi sinh hoạt) vào `RequestCategory`.
- **FR-002**: Hệ thống MUST hỗ trợ lưu trữ `meeting_id` (buổi mới - Meeting B) và `old_meeting_id` (buổi cũ - Meeting A, có thể null nếu đăng ký mới) trong entity `PermissionRequest`.
- **FR-003**: Hệ thống MUST tính toán số ghế khả dụng của một buổi họp theo công thức:
  $$\text{Ghế khả dụng} = \text{MAX\_SEATS} - \left(\text{Số participant active} - \text{Số participant có đơn ABSENCE hợp lệ}\right)$$
- **FR-004**: Hệ thống MUST tự động phê duyệt (Auto-Approve) đơn `CHANGE_MEETING` nếu số ghế khả dụng của Meeting B $> 0$ và thời điểm gửi đơn trước giờ bắt đầu của Meeting B.
- **FR-005**: Hệ thống MUST thực hiện điều phối participant trong một Transaction nguyên tử: rút khỏi Meeting A (nếu có) và thêm vào Meeting B.
- **FR-006**: Hệ thống MUST tự động hủy các đơn xin phép vắng (`ABSENCE`) hoặc xin trễ (`LATE`) của người dùng tại Meeting A cũ khi chuyển sang Meeting B thành công.
- **FR-007**: Giao diện nộp đơn MUST cung cấp danh sách dropdown chọn Meeting hiện tại (kèm tùy chọn "Chưa có buổi học nào") và dropdown chọn Meeting đích hiển thị số ghế còn trống theo thời gian thực.
- **FR-008**: Hệ thống MUST ngăn chặn việc nộp đơn nếu Meeting đích đã bắt đầu hoặc đã đủ số lượng người tham dự tối đa.

### Key Entities

- **PermissionRequest**:
  - `category`: `CHANGE_MEETING`
  - `meeting_id`: ID của buổi họp muốn chuyển sang (Meeting B).
  - `old_meeting_id`: ID của buổi họp cũ (Meeting A, optional).
  - `note`: Lý do đổi ca.
- **Meeting**:
  - `id`, `title`, `start_time`, `end_time`
  - `participants`: Danh sách người tham dự.
- **MeetingParticipant**:
  - `user_id`, `meeting_id`, `status`

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Thành viên có thể hoàn tất nộp đơn và đổi ca sinh hoạt thành công trong dưới 10 giây mà không cần chờ Admin duyệt.
- **SC-002**: Độ chính xác tính toán số lượng ghế trống đạt 100%, tuyệt đối không xảy ra tình trạng vượt quá `MAX_SEATS` ngay cả khi nhiều người nộp đơn cùng lúc.
- **SC-003**: 100% các đơn vắng/trễ cũ tại Meeting A được tự động thu hồi ngay khi đổi ca thành công sang Meeting B.
- **SC-004**: Giao diện hiển thị trực quan số lượng ghế trống còn lại của từng buổi họp sắp tới giúp học viên dễ dàng chọn ca học còn trống.

---

## Assumptions

- Cấu hình số ghế tối đa của phòng học/hệ thống sử dụng giá trị `settings.MAX_SEATS` hiện có trong hệ thống.
- Các buổi họp Meeting B phải được khởi tạo trước trên hệ thống thì thành viên mới có thể thấy và chọn đổi sang.
- Quyền nộp đơn `CHANGE_MEETING` áp dụng cho tất cả các thành viên có tài khoản hợp lệ trong hệ thống.
