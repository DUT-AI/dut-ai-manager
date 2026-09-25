# Feature Specification: Baseline Nghiệp Vụ Domain Meeting (Sinh Hoạt & Họp Nhóm)

**Feature Branch**: `001-meeting-domain`

**Created**: 2026-09-25

**Status**: Draft

**Input**: User description: "Đặc tả toàn bộ luồng nghiệp vụ hiện tại của domain Meeting bao gồm Check-in qua mã thẻ/ảnh, tính Capacity và Job 23:59 tự động tạo vi phạm"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Điểm danh và Ghi nhận sự hiện diện (Priority: P1)

Thành viên tham gia buổi sinh hoạt/họp có thể điểm danh nhanh tại quầy thông qua mã thẻ (RFID/thẻ thành viên) hoặc gửi ảnh nhận diện khuôn mặt. Khi kết thúc sinh hoạt, thành viên có thể thực hiện check-out để ghi nhận thời gian rời phòng.

**Why this priority**: Đây là luồng nghiệp vụ cốt lõi, diễn ra thường xuyên nhất của hệ thống nhằm ghi nhận chính xác sự có mặt của thành viên.

**Independent Test**: Có thể kiểm thử độc lập bằng cách quẹt mã thẻ hoặc gửi ảnh điểm danh cho một buổi họp đang diễn ra, sau đó kiểm tra xem trạng thái của thành viên đã chuyển thành đã điểm danh (`JOINED`) hay chưa.

**Acceptance Scenarios**:

1. **Given** một buổi họp diễn ra từ 14:00 đến 16:00 và thành viên quẹt mã thẻ lúc 14:03, **When** hệ thống xác thực mã thẻ thành công, **Then** hệ thống ghi nhận trạng thái điểm danh đúng giờ và gửi thông báo xác nhận.
2. **Given** một buổi họp bắt đầu lúc 14:00 và thành viên gửi ảnh điểm danh lúc 14:10 (> 5 phút so với giờ bắt đầu), **When** hệ thống ghi nhận điểm danh, **Then** hệ thống đánh dấu là điểm danh trễ và lưu ảnh bằng chứng.
3. **Given** một thành viên đã check-in thành công, **When** thành viên bấm check-out lúc 16:00, **Then** hệ thống cập nhật thời gian check-out và chuyển trạng thái hoàn thành (`COMPLETED`).
4. **Given** mạng chập chờn gửi cùng một mã sự kiện (`client_event_id`) 2 lần liên tiếp, **When** hệ thống xử lý lần thứ 2, **Then** hệ thống nhận diện yêu cầu trùng lặp và bỏ qua không tạo bản ghi mới.

---

### User Story 2 - Tự động đối soát điểm danh và ghi nhận vi phạm lúc 23:59 (Priority: P1)

Hàng ngày vào cuối ngày (23:59), hệ thống tự động quét toàn bộ các buổi sinh hoạt có yêu cầu điểm danh trong ngày, đối chiếu trạng thái điểm danh thực tế với danh sách đơn xin phép đã được duyệt, từ đó cập nhật trạng thái cuối cùng và tự động tạo biên bản vi phạm cho các trường hợp vắng hoặc trễ không phép.

**Why this priority**: Đảm bảo kỷ luật sinh hoạt tự động, loại bỏ việc rà soát thủ công của ban quản lý.

**Independent Test**: Kích hoạt tác vụ đối soát với dữ liệu giả lập (thành viên vắng có phép, vắng không phép, trễ không phép, trễ có phép) và kiểm tra số lượng biên bản vi phạm được sinh ra chính xác.

**Acceptance Scenarios**:

1. **Given** thành viên không điểm danh nhưng đã có đơn xin vắng được chấp thuận, **When** tác vụ 23:59 chạy, **Then** chuyển trạng thái thành vắng có phép (`ABSENT_EXCUSED`) và KHÔNG tạo vi phạm.
2. **Given** thành viên không điểm danh và không có đơn xin phép, **When** tác vụ 23:59 chạy, **Then** chuyển trạng thái thành vắng không phép (`ABSENT_UNEXCUSED`) và TỰ ĐỘNG tạo 01 biên bản vi phạm "Vắng sinh hoạt không phép".
3. **Given** thành viên check-in trễ (> 5 phút) nhưng có đơn xin đi trễ hợp lệ (giờ đến trước hoặc đúng giờ xin phép), **When** tác vụ 23:59 chạy, **Then** chuyển trạng thái thành trễ có phép (`LATE_EXCUSED`) và KHÔNG tạo vi phạm.
4. **Given** thành viên check-in trễ và không có đơn xin phép (hoặc đến muộn hơn giờ đã xin phép), **When** tác vụ 23:59 chạy, **Then** chuyển trạng thái thành trễ không phép (`LATE_UNEXCUSED`) và TỰ ĐỘNG tạo 01 biên bản vi phạm.
5. **Given** thành viên đã check-in đúng giờ nhưng quên check-out khi rời phòng, **When** tác vụ 23:59 chạy, **Then** hệ thống tự động gán thời gian kết thúc buổi họp làm giờ check-out và chuyển trạng thái thành hoàn thành (`COMPLETED`).

---

### User Story 3 - Lên lịch và Quản lý Buổi sinh hoạt / Họp nhóm (Priority: P2)

Người quản trị (Admin) hoặc Trưởng nhóm (Leader) có thể tạo lịch sinh hoạt mới cho cá nhân hoặc cả nhóm (Team), chỉnh sửa thông tin buổi họp (thời gian, tiêu đề, nội dung, yêu cầu điểm danh) hoặc cập nhật thủ công trạng thái của thành viên khi có sự cố đặc biệt.

**Why this priority**: Cung cấp công cụ quản trị dữ liệu lịch họp cho ban điều hành.

**Independent Test**: Tạo một buổi sinh hoạt cho Team A từ giao diện quản lý, kiểm tra xem tất cả thành viên Team A có nằm trong danh sách tham gia không.

**Acceptance Scenarios**:

1. **Given** Admin nhập tiêu đề, thời gian bắt đầu, thời gian kết thúc và chọn Team, **When** bấm tạo buổi họp, **Then** hệ thống tạo lịch sinh hoạt mới và thêm toàn bộ thành viên trong Team vào danh sách tham gia.
2. **Given** lịch họp bị thay đổi giờ, **When** người tạo cập nhật thời gian, **Then** thông tin mới được lưu lại và gửi thông báo cập nhật đến các thành viên liên quan.
3. **Given** một thành viên gặp sự cố thiết bị không thể quẹt thẻ, **When** Admin cập nhật thủ công trạng thái thành viên sang Đã tham gia (`JOINED`), **Then** hệ thống lưu lại trạng thái mới và hiển thị trên bảng điểm danh.

---

### User Story 4 - Giám sát và Cảnh báo Sức chứa Phòng Lab (Priority: P2)

Ban quản lý và các thành viên có thể theo dõi số lượng người đang có mặt thực tế tại phòng Lab và dự báo tình trạng sức chứa trong 30 phút tới theo thời gian thực để tránh quá tải.

**Why this priority**: Giúp điều phối không gian làm việc tại phòng Lab hiệu quả, tránh xung đột lịch sinh hoạt.

**Independent Test**: Gọi yêu cầu lấy thông tin sức chứa khi có 1 người đang ở trong lab, 2 người sắp đến trong 30 phút tới và kiểm tra trạng thái cảnh báo trả về.

**Acceptance Scenarios**:

1. **Given** tổng số người dự kiến có mặt trong phòng nhỏ hơn 2, **When** hệ thống tính toán sức chứa, **Then** trả về trạng thái An toàn (`SAFE`).
2. **Given** tổng số người dự kiến có mặt đạt mức 2 người, **When** hệ thống tính toán, **Then** trả về trạng thái Cảnh báo (`WARNING`).
3. **Given** tổng số người dự kiến có mặt từ 3 người trở lên, **When** hệ thống tính toán, **Then** trả về trạng thái Quá tải (`OVERLOAD`).
4. **Given** giao diện Dashboard đang mở kết nối luồng sự kiện thời gian thực (SSE), **When** có thành viên check-in hoặc check-out, **Then** giao diện tự động cập nhật số lượng người tức thì mà không cần tải lại trang.

---

### User Story 5 - Thông báo đa kênh tự động (Priority: P3)

Thành viên nhận được thông báo tức thì qua các kênh giao tiếp quen thuộc (Discord và Zalo Bot) khi có lịch họp mới, lịch họp bị dời/hủy, hoặc ngay sau khi bản thân điểm danh thành công.

**Why this priority**: Tăng trải nghiệm người dùng, giúp thành viên không bỏ lỡ lịch sinh hoạt.

**Independent Test**: Tạo một buổi họp có gán user ID có liên kết Discord/Zalo, kiểm tra tin nhắn thông báo được gửi đi thành công.

**Acceptance Scenarios**:

1. **Given** thành viên đã liên kết tài khoản Discord, **When** được thêm vào buổi họp mới, **Then** Discord Bot gửi tin nhắn riêng chứa tiêu đề, khung thời gian và ghi chú của buổi họp.
2. **Given** thành viên điểm danh thành công tại phòng Lab, **When** hệ thống ghi nhận dữ liệu, **Then** Bot gửi tin nhắn xác nhận kèm trạng thái (Đúng giờ hay Trễ).

---

### Edge Cases

- **Check-in ngoài khung giờ cho phép**: Người dùng quẹt thẻ trước buổi họp > 30 phút hoặc sau buổi họp > 30 phút. Hệ thống sẽ báo lỗi không tìm thấy buổi họp phù hợp.
- **Trùng lặp sự kiện do lỗi mạng**: Thiết bị quầy gửi nhiều request check-in cùng lúc do retry mạng. Hệ thống dùng `client_event_id` để đảm bảo tính bất biến (idempotent), chỉ ghi nhận 1 lần.
- **Thành viên có nhiều buổi họp cùng ngày**: Job 23:59 xử lý độc lập từng buổi họp và đối chiếu đúng `meeting_id` trong đơn xin phép.
- **Người dùng chưa đăng ký mã thẻ**: Quẹt thẻ chưa đăng ký trên hệ thống sẽ trả về hướng dẫn đăng ký trên trang cá nhân.
- **Tập tin ảnh không hợp lệ hoặc lỗi lưu trữ**: Khi dịch vụ lưu trữ ảnh (MinIO) gặp lỗi, hệ thống phải xử lý an toàn và không làm gián đoạn toàn bộ tiến trình điểm danh.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI cho phép tạo, xem danh sách, xem chi tiết, cập nhật và xóa các buổi sinh hoạt/họp nhóm.
- **FR-002**: Hệ thống PHẢI hỗ trợ gán thành viên tham gia buổi họp theo từng tài khoản cá nhân hoặc tự động theo nhóm (Team).
- **FR-003**: Hệ thống PHẢI hỗ trợ điểm danh qua mã thẻ thành viên (RFID) trong khung thời gian hợp lệ (thời gian hiện tại $\pm 30$ phút so với lịch họp).
- **FR-004**: Hệ thống PHẢI hỗ trợ điểm danh qua hình ảnh/nhận diện khuôn mặt với danh sách một hoặc nhiều người dùng cùng lúc kèm ảnh lưu trữ bằng chứng.
- **FR-005**: Hệ thống PHẢI hỗ trợ cơ chế chống gửi trùng lặp (`client_event_id` / Idempotency Key) để bảo đảm an toàn dữ liệu mạng.
- **FR-006**: Hệ thống PHẢI tự động xác định điểm danh đúng giờ hoặc trễ (mốc quy định: quá 5 phút kể từ thời gian bắt đầu buổi họp được tính là trễ).
- **FR-007**: Hệ thống PHẢI cung cấp tính năng check-out để ghi nhận thời điểm thành viên rời khỏi buổi sinh hoạt.
- **FR-008**: Hệ thống PHẢI hỗ trợ 7 trạng thái tham gia của thành viên: `NOT_JOINED`, `JOINED`, `LATE_EXCUSED`, `LATE_UNEXCUSED`, `ABSENT_EXCUSED`, `ABSENT_UNEXCUSED`, `COMPLETED`.
- **FR-009**: Hệ thống PHẢI chạy tác vụ đối soát tự động lúc 23:59 hàng ngày để quét tất cả các buổi họp yêu cầu điểm danh trong ngày.
- **FR-010**: Tác vụ 23:59 PHẢI tự động liên kết với module Đơn xin phép (`PermissionRequest`) để phân loại có phép / không phép.
- **FR-011**: Tác vụ 23:59 PHẢI tự động tạo biên bản vi phạm (`Violation`) cho các trường hợp vắng không phép, trễ không phép hoặc đến trễ hơn thời gian đã xin phép.
- **FR-012**: Tác vụ 23:59 PHẢI tự động hoàn thành buổi họp (`COMPLETED`) cho các thành viên đã check-in đúng giờ nhưng quên bấm check-out.
- **FR-013**: Hệ thống PHẢI tính toán sức chứa phòng Lab hiện tại và dự báo 30 phút tới dựa trên số lượng người đang có mặt, người sắp đến và người sắp về.
- **FR-014**: Hệ thống PHẢI phân loại sức chứa thành 3 cấp độ: `SAFE` ($<2$), `WARNING` ($=2$), `OVERLOAD` ($\ge 3$).
- **FR-015**: Hệ thống PHẢI phát sự kiện luồng thời gian thực (SSE) khi có biến động điểm danh/check-out để cập nhật giao diện Dashboard.
- **FR-016**: Hệ thống PHẢI tự động kích hoạt thông báo qua Discord và Zalo Bot khi tạo/sửa lịch họp hoặc khi thành viên điểm danh thành công.
- **FR-017**: Người tạo buổi họp hoặc Quản trị viên PHẢI có quyền cập nhật thủ công trạng thái và giờ điểm danh/check-out của từng thành viên.

---

### Key Entities *(include if feature involves data)*

- **Buổi họp (`Meeting`)**: Đại diện cho một sự kiện sinh hoạt hoặc cuộc họp. Thuộc tính chính gồm: tiêu đề, mô tả nội dung, thời gian bắt đầu, thời gian kết thúc, cờ yêu cầu điểm danh (`require_check_in`), người tạo, danh sách thành viên tham gia.
- **Thành viên tham dự (`MeetingParticipant`)**: Đại diện cho sự tham gia của một người dùng trong một buổi họp. Thuộc tính chính: mã người dùng, mã buổi họp, thời gian check-in, thời gian check-out, trạng thái tham dự (`status`), đường dẫn ảnh bằng chứng, mã định danh sự kiện chống lặp (`client_event_id`).
- **Giám sát sức chứa (`CapacityMonitor`)**: Giá trị đại diện cho trạng thái tải phòng Lab. Thuộc tính gồm: số người hiện tại, số người sắp đến (trong 30 phút), số người sắp rời đi (trong 10 phút), sức chứa tối đa (3 người), trạng thái đánh giá (`SAFE`, `WARNING`, `OVERLOAD`).
- **Đơn xin phép (`PermissionRequest`)**: Thực thể liên kết thuộc domain xin phép, chứa thông tin người xin phép, loại đơn (vắng/trễ), buổi họp liên quan và khoảng thời gian xin phép hợp lệ.
- **Biên bản vi phạm (`Violation`)**: Thực thể liên kết thuộc domain vi phạm, được tạo tự động khi phát hiện thành viên vắng/trễ không phép kèm lý do và ngày giờ vi phạm.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% các lượt quẹt thẻ hoặc gửi ảnh điểm danh hợp lệ được ghi nhận trạng thái chính xác trong vòng dưới 2 giây.
- **SC-002**: 100% các trường hợp vắng hoặc trễ không phép trong ngày được tác vụ 23:59 quét và tạo biên bản vi phạm đầy đủ, không bỏ sót.
- **SC-003**: 0% trường hợp thành viên có đơn xin phép hợp lệ đã duyệt bị tạo nhầm vi phạm.
- **SC-004**: Thay đổi trạng thái sức chứa phòng Lab được đồng bộ tức thì đến giao diện Dashboard qua luồng sự kiện thời gian thực với độ trễ dưới 1 giây.
- **SC-005**: 100% các yêu cầu điểm danh trùng lặp (do lỗi mạng gửi lại) bị chặn, không làm sai lệch số liệu thống kê.

---

## Assumptions

- Múi giờ chuẩn của toàn bộ hệ thống tính toán thời gian sinh hoạt và điểm danh là **UTC+7 (Giờ Việt Nam)**.
- Khung thời gian linh hoạt để quẹt thẻ điểm danh là $\pm 30$ phút quanh thời điểm bắt đầu/diễn ra buổi họp.
- Thời gian ân hạn tối đa để tính là điểm danh đúng giờ là **5 phút** kể từ thời điểm bắt đầu buổi họp.
- Sức chứa tiêu chuẩn của phòng Lab nghiên cứu được cấu hình mặc định là **3 người**, bắt đầu cảnh báo khi đạt 2 người.
- Người dùng đã được cấu hình mã thẻ `check_in_card_code`, `discord_id` hoặc `zalo_bot_id` trên hồ sơ cá nhân để nhận diện và nhận thông báo.
