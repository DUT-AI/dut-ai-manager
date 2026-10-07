# Feature Specification: Đơn Xin Đổi Buổi Sinh Hoạt / Meeting (`CHANGE_MEETING`)

**Feature Branch**: `007-change-meeting-permission-request`

**Created**: 2026-10-06

**Last Updated**: 2026-10-07

**Status**: Draft (Clarified)

**Input**: User description: "Thêm chức năng xin đổi meeting trong permission request, cho phép đổi từ meeting A sang meeting B (hoặc đăng ký mới vào meeting B nếu chưa có meeting). Hệ thống tự động kiểm tra số lượng ghế còn lại = MAX_SEAT - (số người đăng ký - số người xin phép vắng). Tự động duyệt và chuyển participant nếu còn chỗ."

## Clarifications

### Session 2026-10-06
- Q: Cơ chế phê duyệt cho loại đơn xin đổi meeting sẽ hoạt động như thế nào? → A: Tự động duyệt ngay (Auto-Approve) nếu Meeting B còn ghế trống (`Ghế còn lại > 0`).
- Q: Cách thức xác định Meeting ban đầu (Meeting A) của người làm đơn sẽ diễn ra như thế nào? → A: Form hiển thị dropdown các buổi Meeting mà user đang tham gia, kèm tùy chọn "Chưa có buổi học nào (Đăng ký mới)", cùng dropdown chọn Meeting đích (Meeting B).
- Q: Khi đổi thành công sang Meeting B, hệ thống xử lý các đơn xin phép cũ ở Meeting A như thế nào? → A: Tự động xóa/hủy đơn vắng hoặc trễ liên quan đến Meeting A cũ.

### Session 2026-10-07 (Business Deep-Dive)
- Q: Thời hạn nộp đơn được tính theo buổi cũ (Meeting A) hay buổi mới (Meeting B)? → A: Chỉ cần đổi trước khi Meeting B bắt đầu (`now < meeting_b.start_time`), kể cả khi Meeting A đã diễn ra xong trong quá khứ.
- Q: Phạm vi chuyển ca có bị giới hạn theo tuần hoặc chủ đề bài học không? → A: Được chọn bất kỳ meeting nào trong tương lai tùy theo nhu cầu của người học.
- Q: Số lần đổi ca có bị giới hạn không? → A: Không giới hạn, thành viên có thể đổi nhiều lần miễn là meeting đích còn chỗ.
- Q: Khi thành viên nộp đơn vắng (ABSENCE) ở Meeting B rồi người khác đổi vào chiếm ghế, nếu người vắng muốn đi học lại thì xử lý thế nào? → A: Không xét trường hợp người xin vắng quay lại (ghế đã nhả cho ca học là hợp lệ để người khác sử dụng).
- Q: Yêu cầu về thông báo và lưu vết kiểm toán (Notification & Audit) sau khi đổi ca? → A:
  1. Gửi thông báo Telegram/Zalo cho chính thành viên (xác nhận ca học mới, thời gian, địa điểm).
  2. Gửi thông báo tới ban quản trị / Host của buổi họp A và B về biến động danh sách tham dự.
  3. Ghi log lịch sử chuyển ca (audit trail) trong chi tiết đơn để hỗ trợ tra cứu khi điểm danh.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Thành viên xin chuyển từ Meeting A sang Meeting B còn chỗ (Priority: P1)

Thành viên đang có tên trong danh sách tham gia của Meeting A nhưng bận đột xuất (hoặc đã lỡ buổi Meeting A trong tuần), muốn chuyển sang tham gia Meeting B trong tương lai. Thành viên mở form xin phép, chọn loại đơn "Xin đổi buổi sinh hoạt", chọn Meeting A hiện tại và Meeting B mong muốn. Hệ thống kiểm tra Meeting B chưa bắt đầu và còn ghế trống, lập tức phê duyệt, rút thành viên khỏi Meeting A và ghi danh vào Meeting B.

**Why this priority**: Đây là luồng nghiệp vụ cốt lõi, giải quyết nhu cầu chuyển ca học/họp linh hoạt của thành viên mà không cần sự can thiệp thủ công từ quản trị viên.

**Independent Test**:
- Tạo 2 buổi họp A và B (B diễn ra trong tương lai, còn 5 chỗ).
- User 1 đang ở A, gửi đơn đổi sang B.
- Kết quả: User 1 không còn ở A (+1 ghế trống cho A), User 1 xuất hiện ở B (-1 ghế trống của B), đơn chuyển sang trạng thái đã phê duyệt thành công.

**Acceptance Scenarios**:
1. **Given** User đang tham gia Meeting A và Meeting B có ghế còn lại > 0, **When** User gửi đơn đổi sang Meeting B trước giờ bắt đầu của B (kể cả khi A đã kết thúc), **Then** Đơn được chấp thuận ngay, User được chuyển sang Meeting B và rút khỏi danh sách tham gia của Meeting A.
2. **Given** Meeting B đã đủ số người tham dự tối đa (ghế còn lại = 0), **When** User cố gắng gửi đơn đổi sang Meeting B, **Then** Hệ thống từ chối yêu cầu và hiển thị thông báo lỗi "Buổi họp đã hết chỗ ngồi".

---

### User Story 2 - Thành viên chưa có buổi học xin đăng ký vào Meeting B (Priority: P2)

Thành viên chưa được phân công hoặc chưa có tên trong buổi họp nào, muốn xin đăng ký tham gia vào Meeting B trong tương lai. Thành viên chọn Meeting gốc là "Chưa có buổi học nào" và chọn Meeting B. Hệ thống kiểm tra chỗ ngồi và thêm thành viên vào Meeting B.

**Why this priority**: Cho phép học viên bổ sung hoặc học bù khi chưa có lịch từ trước.

**Independent Test**:
- User chưa ở trong meeting nào.
- Gửi đơn xin vào Meeting B (còn chỗ).
- Kết quả: User được thêm làm participant của Meeting B.

**Acceptance Scenarios**:
1. **Given** User không thuộc Meeting nào và Meeting B còn chỗ, **When** User chọn "Chưa có buổi học nào" và gửi đơn xin vào B, **Then** Hệ thống thêm User vào Meeting B thành công.

---

### User Story 3 - Tự động dọn dẹp đơn xin vắng cũ khi chuyển ca thành công (Priority: P3)

Trước đó User đã gửi đơn xin vắng (`ABSENCE`) hoặc đơn xin trễ (`LATE`) cho Meeting A. Sau đó, User thấy Meeting B phù hợp và gửi đơn đổi sang B thành công. Hệ thống tự động thu hồi/hủy đơn xin vắng/trễ ở Meeting A để tránh rác dữ liệu và sai lệch thống kê vi phạm.

**Why this priority**: Đảm bảo tính toàn vẹn và nhất quán của dữ liệu điểm danh và quét vi phạm.

**Independent Test**:
- User có đơn xin vắng hoặc đi trễ tại Meeting A.
- Đổi ca sang Meeting B thành công.
- Kết quả: Đơn xin vắng/trễ tại Meeting A bị hủy / vô hiệu hóa.

**Acceptance Scenarios**:
1. **Given** User có đơn xin vắng/trễ đang hiệu lực tại Meeting A, **When** User đổi ca sang Meeting B thành công, **Then** Đơn xin vắng/trễ tại Meeting A được tự động hủy/xóa.

---

### User Story 4 - Thông báo đa kênh và ghi nhật ký kiểm toán (Priority: P2)

Sau khi hệ thống xử lý chuyển ca thành công:
1. Thành viên nhận được tin nhắn xác nhận qua Telegram/Zalo thông báo chi tiết ca học mới (tên buổi, thời gian, phòng họp).
2. Ban quản trị / Host phụ trách của Meeting A nhận được thông báo giảm 1 học viên, Host của Meeting B nhận thông báo tăng 1 học viên.
3. Chi tiết đơn lưu vết lịch sử chuyển đổi (thời gian chuyển, từ ca nào sang ca nào, ai thực hiện) để phục vụ tra cứu khi đối soát điểm danh.

**Why this priority**: Giữ tính minh bạch trong vận hành và đảm bảo cả học viên lẫn người quản lý lớp nắm bắt được thông tin thay đổi kịp thời.

**Acceptance Scenarios**:
1. **Given** Đơn đổi ca sang Meeting B được duyệt thành công, **When** Hệ thống hoàn tất giao dịch, **Then** Tin nhắn thông báo được gửi tới Telegram/Zalo của thành viên và Host liên quan, đồng thời lưu lịch sử vào nhật ký đơn.

---

### Edge Cases

- **Meeting B đã bắt đầu hoặc đã kết thúc**: Hệ thống chặn không cho nộp đơn đổi sang Meeting B nếu thời điểm hiện tại `now >= meeting_b.start_time`.
- **Meeting A đã diễn ra trong quá khứ**: Thành viên vẫn được phép chọn Meeting A cũ để đổi sang Meeting B mới trong tương lai (miễn là Meeting B chưa bắt đầu).
- **Đổi sang chính Meeting đang ở ($A = B$)**: Hệ thống báo lỗi validation ngay tại frontend và backend ("Không thể đổi sang cùng một buổi họp").
- **Đổi ca nhiều lần liên tiếp**: Thành viên có thể đổi từ A sang B, sau đó đổi từ B sang C; mỗi lần đổi hệ thống đều cập nhật lại participant hiện tại và ghi thêm lịch sử luân chuyển ca.
- **Tranh chấp ghế cuối cùng (Race Condition)**: Khi Meeting B chỉ còn đúng 1 ghế và có 2 thành viên cùng gửi đơn đồng thời, cơ chế khóa giao dịch (Transaction Lock) đảm bảo chỉ 1 người thành công, người thứ hai nhận thông báo hết chỗ.
- **Tính toán ghế trống theo đơn vắng**: Một người ở Meeting B có đơn `ABSENCE` hợp lệ thì người đó không chiếm ghế, ghế đó được tính là ghế trống sẵn sàng cho người khác đổi vào.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống MUST bổ sung loại danh mục yêu cầu mới `CHANGE_MEETING` (Đổi buổi sinh hoạt) vào `RequestCategory`.
- **FR-002**: Hệ thống MUST hỗ trợ lưu trữ `meeting_id` (buổi mới - Meeting B) và `old_meeting_id` (buổi cũ - Meeting A, có thể null nếu đăng ký mới) trong entity `PermissionRequest`.
- **FR-003**: Hệ thống MUST tính toán số ghế khả dụng của một buổi họp theo công thức:
  $$\text{Ghế khả dụng} = \text{MAX\_SEATS} - \left(\text{Số participant active} - \text{Số participant có đơn ABSENCE hợp lệ}\right)$$
- **FR-004**: Hệ thống MUST tự động phê duyệt (Auto-Approve) đơn `CHANGE_MEETING` nếu số ghế khả dụng của Meeting B $> 0$ và thời điểm gửi đơn trước giờ bắt đầu của Meeting B (`now < meeting_b.start_time`), không hạn chế thời gian của Meeting A.
- **FR-005**: Hệ thống MUST cho phép thành viên chọn bất kỳ buổi Meeting B nào trong tương lai và không giới hạn số lần nộp đơn đổi ca.
- **FR-006**: Hệ thống MUST thực hiện điều phối participant trong một Transaction nguyên tử: rút khỏi Meeting A (nếu có) và thêm vào Meeting B.
- **FR-007**: Hệ thống MUST tự động hủy các đơn xin phép vắng (`ABSENCE`) hoặc xin trễ (`LATE`) của người dùng tại Meeting A cũ khi chuyển sang Meeting B thành công.
- **FR-008**: Giao diện nộp đơn MUST cung cấp danh sách dropdown chọn Meeting hiện tại (kèm tùy chọn "Chưa có buổi học nào") và dropdown chọn Meeting đích trong tương lai hiển thị số ghế còn trống theo thời gian thực.
- **FR-009**: Hệ thống MUST gửi thông báo tự động (qua kênh Telegram/Zalo cấu hình sẵn) cho thành viên để xác nhận thông tin ca học mới khi đơn được duyệt.
- **FR-010**: Hệ thống MUST gửi thông báo tới Ban quản trị / Host phụ trách của Meeting A và Meeting B về biến động danh sách người tham gia.
- **FR-011**: Hệ thống MUST lưu vết lịch sử chuyển ca (Audit Trail) trong chi tiết đơn (bao gồm thời gian thực hiện, ID ca cũ, ID ca mới, ghi chú).

### Key Entities

- **PermissionRequest**:
  - `category`: `CHANGE_MEETING`
  - `meeting_id`: ID của buổi họp muốn chuyển sang (Meeting B).
  - `old_meeting_id`: ID của buổi họp cũ (Meeting A, optional).
  - `note`: Lý do đổi ca.
  - `history_logs`: Nhật ký lưu vết quá trình chuyển ca.
- **Meeting**:
  - `id`, `title`, `start_time`, `end_time`
  - `participants`: Danh sách người tham dự.
- **MeetingParticipant**:
  - `user_id`, `meeting_id`, `status`

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Thành viên hoàn tất nộp đơn và hệ thống xử lý chuyển ca thành công trong dưới 10 giây mà không cần can thiệp thủ công từ Admin.
- **SC-002**: Độ chính xác tính toán số lượng ghế trống đạt 100%, tuyệt đối không xảy ra tình trạng vượt quá `MAX_SEATS` ngay cả khi nhiều người nộp đơn đồng thời.
- **SC-003**: 100% các đơn vắng/trễ cũ tại Meeting A được tự động thu hồi ngay khi đổi ca thành công sang Meeting B.
- **SC-004**: 100% các giao dịch đổi ca thành công đều gửi thông báo tức thời tới thành viên và Host/Admin liên quan.
- **SC-005**: 100% các thao tác đổi ca được ghi nhận đầy đủ lịch sử kiểm toán phục vụ tra cứu khi điểm danh.
- **SC-006**: Giao diện hiển thị trực quan số lượng ghế trống còn lại của từng buổi họp sắp tới giúp học viên dễ dàng chọn ca học còn trống.

---

## Assumptions

- Cấu hình số ghế tối đa của phòng học/hệ thống sử dụng giá trị `settings.MAX_SEATS` hiện có trong hệ thống.
- Các buổi họp Meeting B phải được khởi tạo trước trên hệ thống thì thành viên mới có thể thấy và chọn đổi sang.
- Quyền nộp đơn `CHANGE_MEETING` áp dụng cho tất cả các thành viên có tài khoản hợp lệ trong hệ thống.
