# Feature Specification: Nhắc Nhở Buổi Họp / Lịch Sinh Hoạt Sắp Diễn Ra Cho Thành Viên (Upcoming Meeting Attendance Reminder)

**Feature Branch**: `023-upcoming-meeting-reminder`

**Created**: 2026-10-21

**Status**: Ready for Planning

**Input**: User description: "tôi muôn thêm chức năng nhắc nhở chuẩn bị đến meeting bạn tham gia @backend/app/reminder/application/scan_and_send_reminders_use_case.py"

## Clarifications

### Session 2026-10-21
- **Q1: Mốc thời gian nhắc nhở trước giờ họp**: Hệ thống nên thiết lập mốc quét nào?
  - **A1**: Tái sử dụng các mốc của hệ thống Task hiện tại (Chiến lược Hybrid): 4 mốc đếm ngược trước giờ họp (`OFFSET_1D` - 24h, `OFFSET_12H` - 12h, `OFFSET_4H` - 4h, `OFFSET_1H` - 1h) kết hợp 4 khung giờ cố định trong ngày (`08:00`, `12:00`, `19:30`, `22:00` giờ UTC+7).
- **Q2: Xử lý thành viên đã có đơn xin vắng được duyệt hoặc đã đổi ca**:
  - **A2**: Tự động loại trừ, KHÔNG gửi thông báo nhắc nhở tham gia cho thành viên có trạng thái vắng có phép (`ABSENT_EXCUSED`) hoặc đã chuyển sang ca họp khác để tránh làm phiền.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Thành viên nhận thông báo nhắc nhở chuẩn bị tham gia buổi họp sắp diễn ra (Priority: P1)

Là một thành viên được phân công tham gia một buổi họp / lịch sinh hoạt, tôi muốn nhận được thông báo nhắc nhở trước khi buổi họp bắt đầu qua đa kênh (Web In-App, Discord Bot DM cá nhân, và Web Push Notification trên thiết bị), nêu rõ thời gian họp, phòng họp/địa điểm, và thời gian còn lại, để tôi có thể chủ động sắp xếp công việc, chuẩn bị tài liệu, có mặt đúng giờ và thực hiện điểm danh, tránh bị ghi nhận vi phạm đi trễ hoặc vắng mặt không phép.

**Why this priority**: Đây là giá trị cốt lõi nhất của tính năng. Giúp giải quyết trực tiếp tình trạng thành viên quên lịch sinh hoạt, giảm thiểu đáng kể số ca vi phạm kỷ luật phòng ban.

**Independent Test**:
- Tạo một buổi họp có thời gian bắt đầu sắp diễn ra và thêm thành viên vào danh sách tham gia.
- Kích hoạt quy trình quét thông báo nhắc nhở.
- Xác minh thành viên nhận được thông báo nhắc nhở với đầy đủ thông tin: tên buổi họp, thời gian bắt đầu theo giờ UTC+7, đếm ngược thời gian còn lại, địa điểm/phòng họp và liên kết truy cập trang buổi họp.

**Acceptance Scenarios**:
1. **Given** thành viên có tên trong danh sách tham gia một buổi họp sắp diễn ra trong ngày, **When** hệ thống kích hoạt quét đến mốc thời gian nhắc nhở trước giờ bắt đầu, **Then** thành viên nhận được thông báo nhắc nhở qua Web In-App và tin nhắn Discord DM cá nhân.
2. **Given** thành viên nhấp vào thông báo trên Web hoặc tin nhắn Discord, **When** hệ thống điều hướng, **Then** mở trực tiếp trang chi tiết buổi họp hiển thị thông tin thời gian, địa điểm và nút điểm danh (check-in).
3. **Given** thành viên đã thực hiện điểm danh (check-in) thành công trước giờ họp, **When** hệ thống quét các mốc nhắc nhở tiếp theo của buổi họp đó, **Then** hệ thống tự động nhận biết và bỏ qua không gửi thông báo trùng lặp.

---

### User Story 2 - Tự động loại trừ thành viên đã có đơn xin vắng được duyệt hoặc đã đổi ca (Priority: P2)

Là một thành viên đã xin phép vắng sinh hoạt và đã được phê duyệt, hoặc đã chuyển thành công sang một ca sinh hoạt khác, tôi không muốn nhận thông báo nhắc nhở tham gia của buổi họp cũ để tránh gây bối rối, nhầm lẫn và phiền hà.

**Why this priority**: Đảm bảo sự chính xác của nghiệp vụ, ngăn chặn thông báo rác và mang lại trải nghiệm chuyên nghiệp cho thành viên.

**Independent Test**:
- Thiết lập một buổi họp với 2 thành viên: Thành viên A (chờ tham gia thông thường) và Thành viên B (đã có đơn xin vắng được duyệt `ABSENT_EXCUSED` hoặc đã chuyển sang buổi họp khác).
- Chạy tiến trình quét nhắc nhở.
- Xác minh chỉ có Thành viên A nhận thông báo, Thành viên B được loại trừ hoàn toàn khỏi danh sách gửi.

**Acceptance Scenarios**:
1. **Given** thành viên có trạng thái vắng có phép (`ABSENT_EXCUSED`) trong buổi họp, **When** hệ thống quét nhắc nhở, **Then** hệ thống bỏ qua thành viên này và không gửi bất kỳ thông báo nào.
2. **Given** thành viên đã chuyển sang ca họp khác thành công, **When** quét buổi họp ban đầu, **Then** thành viên không nhận thông báo của buổi ban đầu mà sẽ chỉ nhận thông báo khi đến lịch của buổi họp mới.

---

### User Story 3 - Quản trị viên theo dõi trạng thái quét và điều phối nhắc nhở cuộc họp (Priority: P3)

Là một Quản trị viên / Ban điều hành, tôi muốn theo dõi số lượng thông báo nhắc nhở cuộc họp được gửi thành công, số lượng bỏ qua do đã điểm danh hoặc đã xin phép, đồng thời có thể chạy thử nghiệm (dry-run) hoặc kích hoạt quét thủ công khi cần thông báo đột xuất cho toàn bộ người tham gia.

**Why this priority**: Giúp ban quản trị kiểm soát chất lượng vận hành và xử lý nhanh chóng trong các trường hợp cần triệu tập họp gấp.

**Independent Test**:
- Quản trị viên thực hiện kích hoạt quét thủ công thông qua bảng điều khiển hoặc API quản trị.
- Kiểm tra báo cáo tổng kết trả về đầy đủ số lượng cuộc họp được quét, số thông báo gửi thành công và danh sách chi tiết các thành viên được nhắc nhở.

**Acceptance Scenarios**:
1. **Given** quản trị viên kích hoạt quét nhắc nhở thủ công, **When** tiến trình hoàn tất, **Then** hệ thống trả về kết quả tổng hợp chi tiết gồm: tổng số cuộc họp được quét, tổng số thông báo đã gửi, số lượng bỏ qua và số lượng thất bại nếu có lỗi mạng.

---

### Edge Cases

- **Buổi họp bị dời lịch hoặc hủy**: Nếu buổi họp được điều chỉnh thời gian bắt đầu hoặc bị hủy trước khi diễn ra, hệ thống tự động cập nhật mốc quét theo thời gian mới và không gửi nhắc nhở cho mốc thời gian cũ.
- **Chống gửi trùng lặp (Idempotency)**: Cùng một buổi họp và cùng một mốc thời gian nhắc nhở, hệ thống đảm bảo mỗi thành viên chỉ nhận duy nhất 1 lần thông báo, kể cả khi tiến trình quét được kích hoạt nhiều lần liên tiếp.
- **Thành viên khóa nhận tin nhắn Discord DM**: Nếu thành viên chặn tin nhắn từ Bot hoặc chưa liên kết Discord, hệ thống ghi nhận trạng thái lỗi phân phối Discord nhưng vẫn đảm bảo thông báo Web In-App và Web Push được tạo và chuyển phát thành công (Fault Isolation).
- **Buổi họp không yêu cầu điểm danh (`require_check_in = False`)**: Hệ thống vẫn gửi thông báo nhắc nhở tham gia với nội dung phù hợp (nhắc thời gian và link/phòng họp), không hiển thị cảnh báo về quy chế điểm danh.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI có khả năng tự động quét các buổi họp sắp diễn ra và xác định chính xác danh sách các thành viên dự kiến tham gia.
- **FR-002**: Hệ thống PHẢI gửi thông báo nhắc nhở đồng bộ qua các kênh truyền thông hiện có của nền tảng:
  - Thông báo Web In-App: Lưu trữ trong hệ thống thông báo hiển thị trên Trang Quản lý Thông báo (`/dashboard/notifications`) với phân loại Cuộc họp.
  - Tin nhắn riêng tư Discord DM: Gửi từ Discord Bot kèm thẻ thông tin chi tiết (Embed).
  - Thông báo đẩy Web Push: Gửi đến các thiết bị đã đăng ký nhận thông báo (PWA/trình duyệt).
- **FR-003**: Hệ thống PHẢI áp dụng cơ chế quét thời gian nhắc nhở theo chiến lược Hybrid thống nhất:
  - 4 mốc đếm ngược trước giờ bắt đầu cuộc họp: `OFFSET_1D` (24 giờ trước), `OFFSET_12H` (12 giờ trước), `OFFSET_4H` (4 giờ trước), và `OFFSET_1H` (1 giờ trước).
  - 4 khung giờ cố định trong ngày diễn ra cuộc họp: `FIXED_0800` (08:00 sáng), `FIXED_1200` (12:00 trưa), `FIXED_1930` (19:30 tối), và `FIXED_2200` (22:00 đêm).
- **FR-004**: Hệ thống PHẢI tự động loại trừ các thành viên không cần nhận thông báo:
  - Thành viên có trạng thái vắng có phép (`ABSENT_EXCUSED`) đã được ban cán sự duyệt.
  - Thành viên đã hoàn tất chuyển ca sang buổi họp khác.
  - Thành viên đã thực hiện điểm danh hoặc hoàn thành buổi họp (`JOINED`, `COMPLETED`).
- **FR-005**: Nội dung thông báo nhắc nhở cuộc họp PHẢI thể hiện rõ: Tiêu đề buổi họp, thời gian bắt đầu theo giờ UTC+7, thời gian đếm ngược còn lại, phòng họp hoặc liên kết trực tuyến, và đường dẫn hành động trực tiếp.
- **FR-006**: Hệ thống PHẢI đảm bảo cơ chế chống trùng lặp (Deduplication) và kiểm soát giãn cách (Cooldown 3 giờ): một thành viên không nhận nhiều hơn một thông báo cho cùng một mốc của một buổi họp. Mốc khẩn cấp 1 giờ trước họp (`OFFSET_1H`) được miễn trừ giới hạn giãn cách cooldown để đảm bảo gửi kịp thời.
- **FR-007**: Khi người dùng nhấn vào thông báo trên Web hoặc trên thông báo đẩy, hệ thống PHẢI tự động đánh dấu thông báo là đã đọc và điều hướng trực tiếp đến trang chi tiết buổi họp tương ứng (`/dashboard/meetings/{meeting_id}`).
- **FR-008**: Hệ thống PHẢI cung cấp cơ chế cho Quản trị viên kích hoạt kiểm tra quét nhắc nhở và xem nhật ký tổng hợp các thông báo đã gửi.

### Key Entities *(include if feature involves data)*

- **Meeting Reminder Item**: Đại diện cho một thông báo nhắc nhở cuộc họp sắp tới, bao gồm định danh buổi họp, thành viên nhận thông báo, thời điểm bắt đầu cuộc họp, mốc nhắc nhở được kích hoạt, liên kết điều hướng và trạng thái gửi.
- **Participant Attendance State**: Bản ghi thể hiện trạng thái tham gia của thành viên đối với buổi họp (Chưa tham gia, Đã điểm danh, Vắng có phép, Đã đổi ca).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% thành viên trong danh sách tham gia nhận được thông báo nhắc nhở cuộc họp trước giờ bắt đầu qua ít nhất một kênh thông báo đang hoạt động.
- **SC-002**: Tỷ lệ thành viên vắng mặt không phép hoặc trễ giờ sinh hoạt giảm tối thiểu 30% sau 1 tháng triển khai tính năng nhắc nhở.
- **SC-003**: 0 trường hợp phát sinh thông báo trùng lặp cho cùng một thành viên tại cùng một mốc nhắc nhở của một buổi họp.
- **SC-004**: 100% thành viên có trạng thái vắng có phép hoặc đã đổi ca không bị gửi thông báo nhắc nhở tham gia buổi họp cũ.
- **SC-005**: Thao tác nhấp vào thông báo để mở trang chi tiết cuộc họp phản hồi tức thì dưới 1 giây.

## Assumptions

- Toàn bộ thời gian hiển thị và so sánh tính toán vận hành theo múi giờ chuẩn UTC+7 (Asia/Ho_Chi_Minh).
- Thành viên đã được xếp lịch tham gia buổi họp trước khi tiến trình quét thông báo diễn ra.
- Hạ tầng gửi thông báo (Discord Bot, Web In-App, Web Push) kế thừa từ hệ thống thông báo chung của dự án.
