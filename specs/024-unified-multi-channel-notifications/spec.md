# Feature Specification: Hệ Thống Điều Phối Thông Báo Đa Kênh Hợp Nhất (Unified Multi-Channel Notifications)

**Feature Branch**: `024-unified-multi-channel-notifications`

**Created**: 2026-10-22

**Status**: Ready for Planning

**Input**: User description: "plan hay đó hãy tạo nghiệp vụ cho tôi: Kiến trúc Unified Notification Hub (Event-Driven + Multi-Channel Adapters): Tích hợp In-App (DB), Discord, Zalo, Web Push vào một Dispatcher duy nhất tại shared layer, các Domain chỉ cần phát Event/Payload. Một khi đã thông báo sẽ thông báo cho zalo bot, in app, discord bot cho mọi nghiệp vụ: tạo meeting, giao bài tập về nhà, điểm cộng, vi phạm, hóa đơn, nhắc hạn chót."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Nhận thông báo đa kênh đồng bộ cho mọi biến động nghiệp vụ (Priority: P1)

Khi có bất kỳ biến động nghiệp vụ nào xảy ra trong hệ thống (được giao bài tập mới, có lịch họp mới, bị ghi nhận vi phạm, được cộng điểm rèn luyện, hoặc phát hành hóa đơn học phí/tiền quỹ), thành viên sẽ nhận được thông báo đồng thời trên toàn bộ các kênh mà họ đã kết nối:
1. Thông báo nội bộ (In-App) hiển thị trên Web Dashboard và Zalo Mini App.
2. Tin nhắn riêng qua Discord Bot (nếu đã liên kết Discord).
3. Tin nhắn riêng qua Zalo Bot (nếu đã liên kết Zalo).
4. Thông báo đẩy trên màn hình thiết bị (Web Push PWA nếu đã cấp quyền).

Nội dung thông báo rõ ràng, sinh động (kèm meme minh họa phù hợp), hiển thị chi tiết nội dung và có nút/liên kết điều hướng trực tiếp đến trang chi tiết của nghiệp vụ đó.

**Why this priority**: Đây là giá trị cốt lõi giải quyết triệt để sự thiếu nhất quán hiện tại, giúp thành viên không bao giờ bỏ lỡ thông tin quan trọng dù họ đang hoạt động trên nền tảng nào.

**Independent Test**: Kích hoạt lần lượt các sự kiện: tạo bài tập, tạo buổi họp, ghi nhận vi phạm, cộng điểm, tạo hóa đơn. Kiểm tra tài khoản thành viên liên kết nhận được thông báo trên tất cả các kênh In-App, Discord, Zalo và Web Push với đầy đủ tiêu đề, nội dung và link điều hướng.

**Acceptance Scenarios**:

1. **Given** Học viên đã liên kết Discord và Zalo Bot, **When** Giảng viên giao bài tập mới, **Then** Học viên nhận được thông báo ngay lập tức trên Discord, Zalo Bot, Web Push và thấy thông báo xuất hiện trong danh sách thông báo trên Web Dashboard/Zalo Mini App.
2. **Given** Ban quản trị tạo một hóa đơn thanh toán quỹ, **When** Hóa đơn được phát hành, **Then** Thành viên nhận được thông báo chi tiết số tiền, hạn nộp kèm mã thanh toán trên toàn bộ các kênh liên kết và In-App.
3. **Given** Thành viên được cộng điểm thưởng hoặc bị ghi nhận vi phạm, **When** Sự kiện phát sinh, **Then** Hệ thống gửi thông báo tức thì kèm hình ảnh minh họa cảm xúc phù hợp đến toàn bộ các kênh liên kết.

---

### User Story 2 - Quản lý và theo dõi danh sách thông báo In-App (Priority: P1)

Thành viên truy cập Web Dashboard hoặc Zalo Mini App có thể xem trung tâm thông báo (Notification Center):
- Xem danh sách toàn bộ các thông báo đã nhận, sắp xếp theo thời gian mới nhất.
- Phân biệt trực quan trạng thái đã đọc và chưa đọc thông qua huy hiệu (badge) đếm số lượng thông báo chưa đọc.
- Lọc thông báo theo danh mục nghiệp vụ (Học tập, Họp hành, Điểm thưởng, Vi phạm, Tài chính/Hóa đơn).
- Thao tác đánh dấu một thông báo là đã đọc hoặc đánh dấu tất cả là đã đọc.
- Bấm vào thông báo để chuyển hướng ngay đến trang chi tiết của tác vụ liên quan.

**Why this priority**: Đảm bảo người dùng luôn có một nơi tập trung lưu trữ lịch sử tương tác, không bị mất dấu thông tin khi tin nhắn chat (Discord/Zalo) bị trôi.

**Independent Test**: Đăng nhập tài khoản người dùng có thông báo mới -> Kiểm tra số lượng badge chưa đọc -> Bấm đọc thông báo -> Kiểm tra số lượng badge giảm đi và trạng thái cập nhật chính xác.

**Acceptance Scenarios**:

1. **Given** Người dùng có 3 thông báo mới chưa đọc, **When** Đăng nhập vào hệ thống, **Then** Biểu tượng chuông thông báo hiển thị số 3 màu đỏ.
2. **Given** Người dùng mở danh sách thông báo và bấm vào 1 thông báo, **When** Thao tác thành công, **Then** Hệ thống đánh dấu thông báo đó đã đọc và chuyển hướng người dùng đến đúng trang nghiệp vụ.
3. **Given** Người dùng bấm "Đánh dấu tất cả là đã đọc", **When** Xác nhận thành công, **Then** Tất cả thông báo chuyển sang trạng thái đã đọc và huy hiệu đếm trở về 0.

---

### User Story 3 - Nhắc việc định kỳ đa kênh không bỏ sót (Priority: P2)

Hệ thống quét định kỳ các nhiệm vụ sắp đến hạn (bài tập chưa nộp, ca trực nhật sắp tới, đánh giá cuộc họp chưa hoàn tất, hoặc cuộc họp sắp diễn ra trong 30-60 phút tới). Khi phát hiện nhiệm vụ cần nhắc nhở, hệ thống tự động phát thông báo nhắc nhở qua toàn bộ các kênh (In-App, Discord, Zalo Bot, Web Push).

**Why this priority**: Nâng cấp hệ thống nhắc việc tự động hiện có để hỗ trợ toàn diện cả kênh Zalo Bot (thay vì chỉ Discord như trước), tăng tỷ lệ hoàn thành nhiệm vụ đúng hạn của học viên.

**Independent Test**: Tạo một bài tập hoặc buổi họp sắp diễn ra -> Chạy tiến trình quét nhắc việc -> Xác minh học viên nhận được thông báo nhắc nhở trên cả Discord, Zalo Bot, Web Push và In-App DB.

**Acceptance Scenarios**:

1. **Given** Cuộc họp sắp diễn ra trong vòng 60 phút, **When** Hệ thống quét định kỳ chạy, **Then** Thành viên tham gia nhận được thông báo nhắc nhở chuẩn bị kèm link phòng họp trên Discord, Zalo Bot, Web Push và In-App.
2. **Given** Học viên chưa nộp bài tập khi còn 12 giờ trước hạn chót, **When** Tiến trình quét kích hoạt, **Then** Học viên nhận được tin nhắn nhắc hạn chót trên tất cả các kênh liên kết.

---

### User Story 4 - Cách ly lỗi và Đảm bảo độ tin cậy khi gửi tin (Priority: P2)

Khi hệ thống phân phối thông báo đến nhiều kênh bên ngoài (Discord, Zalo, Web Push), nếu một kênh gặp sự cố (ví dụ: Discord bị lỗi mạng/rate limit, hoặc người dùng chưa kích hoạt Zalo Bot, hoặc subscription Web Push hết hạn):
- Lỗi của kênh đó tuyệt đối không ảnh hưởng đến việc gửi thông báo thành công ở các kênh còn lại.
- Lỗi không làm gián đoạn hoặc thất bại giao dịch nghiệp vụ chính (tạo meeting, nộp bài, thanh toán).
- Hệ thống luôn đảm bảo lưu thành công bản ghi thông báo In-App vào cơ sở dữ liệu làm nguồn lưu trữ đảm bảo.

**Why this priority**: Bảo vệ tính ổn định và tính sẵn sàng cao của hệ thống nghiệp vụ cốt lõi, ngăn chặn việc lỗi API bên thứ 3 làm treo hoặc sập ứng dụng.

**Independent Test**: Giả lập tình huống tài khoản người dùng chặn bot Discord hoặc Zalo Bot trả về lỗi -> Thực hiện tạo bài tập mới -> Kiểm tra nghiệp vụ tạo bài tập vẫn thành công 100%, thông báo In-App vẫn lưu bình thường, và các kênh còn lại vẫn nhận được tin.

**Acceptance Scenarios**:

1. **Given** Kênh Discord của người dùng bị chặn DM (Direct Message blocked), **When** Có thông báo vi phạm mới phát ra, **Then** Hệ thống ghi nhận cảnh báo, thông báo vẫn được gửi thành công qua Zalo Bot và lưu vào In-App DB.
2. **Given** Dịch vụ Zalo Bot phản hồi chậm hoặc tạm thời mất kết nối, **When** Có thông báo buổi họp mới, **Then** Giao dịch tạo buổi họp không bị nghẽn, Discord và In-App nhận tin ngay lập tức.

---

### Edge Cases

- **Người dùng chưa liên kết bất kỳ kênh mạng xã hội nào (Không Discord, Không Zalo)**: Hệ thống vẫn lưu trữ thông báo In-App vào cơ sở dữ liệu bình thường, người dùng vẫn xem được đầy đủ khi đăng nhập Web hoặc Mini App.
- **Gửi thông báo đồng loạt cho nhiều người (Broadcast / Batch Notification)**: Khi tạo buổi họp chung cho 100 thành viên, hệ thống xử lý phân phối theo lô (batch) bất đồng bộ, tránh nghẽn bộ nhớ hoặc chạm ngưỡng giới hạn tần suất (Rate Limit) của Discord/Zalo.
- **Trùng lặp thông báo nhắc việc định kỳ**: Đối với thông báo định kỳ (scanners), hệ thống áp dụng cơ chế kiểm tra chặn lặp để cùng một giai đoạn nhắc nhở (ví dụ mốc 24h) không gửi nhiều hơn 1 lần cho cùng một người và nhiệm vụ.
- **Nội dung thông báo chứa ký tự đặc biệt hoặc quá dài**: Hệ thống tự động cắt tỉa (truncate) an toàn theo giới hạn ký tự tối đa của từng nền tảng (Discord Embed: 4096 ký tự, Zalo text message: 2000 ký tự) mà không làm lỗi định dạng.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI lưu trữ 100% các thông báo phát ra vào cơ sở dữ liệu trung tâm (In-App Notification) để hiển thị lịch sử trên Web Dashboard và Zalo Mini App.
- **FR-002**: Hệ thống PHẢI cung cấp một cổng điều phối thông báo tập trung (Unified Notification Hub / Dispatcher) nhận yêu cầu từ tất cả các module nghiệp vụ trong hệ thống.
- **FR-003**: Cổng điều phối PHẢI tự động nhận diện và gửi thông báo song song đến tất cả các kênh được kích hoạt của người dùng bao gồm: In-App DB, Discord Bot (DM/Room), Zalo Bot, và Web Push.
- **FR-004**: Tất cả các module nghiệp vụ (Meeting, Homework, Violation, Bonus Point, Billing, Task Reminder) PHẢI sử dụng một cấu trúc dữ liệu chuẩn hóa (`NotificationPayload`) khi yêu cầu phát thông báo, bao gồm: người nhận, tiêu đề, nội dung, danh mục, mức độ ưu tiên, hình ảnh minh họa, và liên kết hành động.
- **FR-005**: Hệ thống PHẢI hỗ trợ các danh mục thông báo chuẩn hóa: Học tập (`HOMEWORK`), Sinh hoạt/Họp (`MEETING`), Trực nhật (`DUTY`), Kỷ luật/Vi phạm (`VIOLATION`), Khen thưởng (`BONUS_POINT`), Tài chính/Hóa đơn (`BILLING`), Đơn xin phép (`PERMISSION_REQUEST`), và Hệ thống (`SYSTEM`).
- **FR-006**: Việc gửi thông báo đến các kênh bên ngoài (Discord, Zalo, Web Push) PHẢI được thực thi bất đồng bộ, không làm chậm hoặc chặn luồng xử lý chính của người dùng.
- **FR-007**: Hệ thống PHẢI áp dụng cơ chế cách ly lỗi (Fault Isolation) hoàn toàn giữa các kênh: sự cố hoặc thất bại ở một kênh không làm gián đoạn các kênh còn lại.
- **FR-008**: Hệ thống PHẢI cung cấp giao diện lập trình (API) cho phép người dùng:
  - Lấy danh sách thông báo cá nhân có phân trang và bộ lọc theo danh mục / trạng thái đọc.
  - Lấy số lượng thông báo chưa đọc.
  - Đánh dấu đã đọc một thông báo cụ thể.
  - Đánh dấu đã đọc toàn bộ thông báo.
- **FR-009**: Hệ thống PHẢI hỗ trợ đính kèm hình ảnh minh họa (Meme assets có sẵn trong kho lưu trữ hoặc URL bên ngoài) tương ứng với từng ngữ cảnh nghiệp vụ.
- **FR-010**: Hệ thống PHẢI hỗ trợ điều phối thông báo nhóm (Room / Channel Notification) cho các sự kiện chung của ban quản trị (như đơn xin phép mới, báo cáo tổng hợp).

---

### Key Entities *(include if feature involves data)*

- **Notification (Thông báo)**: Đại diện cho một bản ghi thông báo gửi đến người dùng.
  - Các thuộc tính chính: Mã định danh, Mã người nhận, Tiêu đề, Nội dung, Danh mục (`category`), Mức độ cảnh báo (`level`: INFO, SUCCESS, WARNING, CRITICAL), Liên kết hành động (`action_url`), Trạng thái đã đọc (`is_read`), Thời gian đọc (`read_at`), Dữ liệu tham chiếu nguồn (`metadata_json`: lưu loại tác vụ, mã tác vụ liên quan), và Thời gian tạo.
- **NotificationPayload (Dữ liệu yêu cầu thông báo)**: Cấu trúc trao đổi dữ liệu chuẩn giữa các tầng ứng dụng và cổng điều phối thông báo.
  - Các thuộc tính: `user_id`, `title`, `content`, `category`, `level`, `image_asset`, `image_url`, `action_url`, `fields`, `color_hex`.
- **PushSubscription (Đăng ký Web Push)**: Quản lý thiết bị nhận thông báo đẩy qua trình duyệt của người dùng (PWA).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% các sự kiện nghiệp vụ trong toàn hệ thống (Meeting, Homework, Violation, Bonus Point, Billing, Task Reminder) đều được tự động lưu vào danh sách thông báo In-App.
- **SC-002**: Người dùng nhận được thông báo trên các kênh đã kết nối (Discord, Zalo, Web Push) trong vòng **dưới 3 giây** kể từ khi sự kiện nghiệp vụ phát sinh.
- **SC-003**: Tỷ lệ giao dịch nghiệp vụ bị gián đoạn hoặc thất bại do sự cố từ nhà cung cấp thông báo bên ngoài (Discord/Zalo down, quá tải) là **0%**.
- **SC-004**: Thời gian cần thiết để một kỹ sư tích hợp thêm thông báo cho một tính năng nghiệp vụ mới giảm từ vài giờ xuống **dưới 15 phút** nhờ cơ chế chuẩn hóa qua Hub và Payload chung.
- **SC-005**: 100% các thông báo gửi đến Discord và Zalo đều có liên kết điều hướng chính xác về ứng dụng Web hoặc Zalo Mini App.

---

## Assumptions

- Người dùng đã được cấp tài khoản trên hệ thống và có ID định danh duy nhất.
- Để nhận được thông báo qua Discord hoặc Zalo Bot, người dùng cần thực hiện liên kết tài khoản Discord/Zalo tương ứng trong hồ sơ cá nhân.
- Hệ thống chạy trên môi trường có kết nối mạng ổn định với các dịch vụ Discord API và Zalo Bot Webhook API.
- Các tài nguyên hình ảnh meme đã được chuẩn bị sẵn trong thư mục tài sản dùng chung (`backend/app/assets`).
- Hệ thống áp dụng múi giờ chuẩn UTC+7 (Asia/Ho_Chi_Minh) cho toàn bộ thời gian hiển thị trong nội dung thông báo.
