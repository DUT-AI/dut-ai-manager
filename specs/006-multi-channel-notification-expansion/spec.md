# Feature Specification: Nâng Cấp Hệ Thống Thông Báo Đa Kênh (Discord & Zalo) Cho Các Use Case Hiện Có

**Feature Branch**: `006-multi-channel-notification-expansion`

**Created**: 2026-10-02

**Status**: Ready for Planning

**Input**: User description: "hãy nâng cấp hệ thống thông báo bằng discord và zalo, hệ thống thông báo được sử dụng để nhắc nhở người dùng ở nhiều use case, hiện tại có ít rất ít trường hợp sử dụng thông báo này. Cập nhật: Trước mắt chỉ tập trung nâng cấp các use case hiện có (Meeting, Homework, Violation, Bonus Point, Permission Request, Billing/Hóa đơn & Thanh toán thành công), không tạo use case mới ngoài hệ thống và tích hợp sử dụng kho ảnh meme/assets trong `backend/app/assets`."

## Clarifications

### Session 2026-10-02
- **Phạm vi use case (Scope)**: Nâng cấp chất lượng, độ hoàn thiện, tính thẩm mỹ và độ tin cậy cho các luồng thông báo của **toàn bộ các use case hiện có** trong hệ thống:
  1. **Homework**: Giao bài tập mới (`HomeworkAssigned`), Chấm điểm/Nhận xét bài tập (`HomeworkGraded`).
  2. **Violation**: Lập biên bản vi phạm mới (`ViolationCreated`), Hủy bỏ/Cập nhật vi phạm (`ViolationUpdated`).
  3. **Bonus Point**: Cộng/trừ điểm thưởng (`BonusPointCreated`, `BonusPointUpdated`, `BonusPointDeleted`).
  4. **Meeting**: Tạo buổi học mới (`MeetingCreated`), Cập nhật lịch học (`MeetingUpdated`), Điểm danh thành công (`ParticipantCheckedIn`).
  5. **Permission Request**: Gửi đơn xin phép vắng/trễ/hoãn bài (`PermissionRequestCreated`).
  6. **Billing / Hóa đơn & Thanh toán**:
     - **Tạo & Nhắc nhở hóa đơn (Invoice Created / Pending Reminder)**: Thông báo khi có hóa đơn mới phát hành (tiền quỹ, phạt vi phạm) kèm mã chuyển khoản QR/SePay.
     - **Thanh toán thành công (Payment Succeeded)**: Thông báo xác nhận ngay khi SePay webhook khớp giao dịch chuyển khoản thành công.
- **Chiến lược phân phối kênh**: Luôn gửi song song cả Discord và Zalo cho mọi use case khi người dùng đã liên kết ID tương ứng.
- **Nguồn Hình ảnh & Meme Assets (`backend/app/assets`)**: Tận dụng trực tiếp bộ hình ảnh meme có sẵn trong `backend/app/assets` để làm hình ảnh minh họa/banner sinh động cho từng ngữ cảnh cụ thể:
  - **Bài tập mới / Học bài**: `meme-hoc-bai.webp`, `meme-lam-viec.webp`, `meme-lam-viec-2.jpeg`
  - **Vi phạm kỷ luật / Đòi phạt**: `meme-doi-no-2.jpg`, `meme-khoc.webp`, `meme-khoc-2.jpg`
  - **Cộng/Trừ Điểm Thưởng / Tiền quỹ & Nhắc Hóa đơn**: `meme-xin-tien.jpeg`, `meme-ngac-nhien.jpeg`
  - **Thanh toán thành công**: `meme-lam-viec-3.jpeg`, `meme-lam-viec-4.jpeg`
  - **Nhắc nhở họp / Đơn xin phép**: `anh-nhac-em-meme-9.webp`, `meme-met-moi-lam-viec.jpg`
- **Cơ chế cách ly lỗi & Retry**: Tách biệt hoàn toàn luồng xử lý gửi tin của từng kênh (Discord / Zalo). Lỗi ở kênh này (như rate limit, token lỗi, user chặn bot) tuyệt đối không ảnh hưởng đến việc gửi tin nhắn thành công ở kênh kia. Tự động áp dụng cơ chế Retry có Exponential Backoff (tối đa 3 lần) cho từng kênh độc lập.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Nâng cấp thông báo Hóa đơn & Xác nhận Thanh toán thành công (Billing & Payment) (Priority: P1)

Khi Admin/Hệ thống tạo hóa đơn hàng tháng hoặc xuất hóa đơn vi phạm/quỹ (`InvoiceCreated`), người dùng nhận được thông báo chi tiết hóa đơn (số tiền, hạn nộp, mã chuyển khoản, hướng dẫn QR) kèm meme nhắc nhở (`meme-xin-tien.jpeg`). Khi người dùng chuyển khoản và SePay webhook xác nhận khớp tiền thành công (`InvoicePaid`), hệ thống gửi ngay thông báo "Thanh toán thành công" kèm meme chúc mừng (`meme-lam-viec-3.jpeg`) đến cả Discord và Zalo của người nộp.

**Why this priority**: Minh bạch tài chính, giúp thành viên thanh toán đúng hạn và yên tâm nhận biên nhận điện tử ngay sau khi chuyển khoản.

**Independent Test**:
- Tạo một hóa đơn cho học viên -> Kiểm tra tin nhắn thông báo hóa đơn kèm mã `DUTxxxxxx` và meme `meme-xin-tien.jpeg` được gửi đến Discord & Zalo.
- Giả lập SePay webhook thanh toán đủ tiền -> Kiểm tra thông báo thanh toán thành công gửi tức thì đến Discord & Zalo của học viên.

**Acceptance Scenarios**:

1. **Given** Hóa đơn mới được tạo cho học viên, **When** sự kiện phát sinh, **Then** học viên nhận được thông báo chi tiết số tiền, lý do thu, mã thanh toán kèm ảnh `meme-xin-tien.jpeg` trên Discord và Zalo.
2. **Given** Học viên chuyển khoản qua ngân hàng, **When** SePay webhook xác thực giao dịch hợp lệ, **Then** hệ thống cập nhật trạng thái `PAID` và gửi thông báo xác nhận thanh toán thành công đến cả 2 kênh của học viên.

---

### User Story 2 - Nâng cấp thông báo Bài tập (Homework) qua Discord và Zalo kèm meme học tập sinh động (Priority: P1)

Khi học viên được giao bài tập mới (`HomeworkAssigned`) hoặc được chấm điểm bài tập (`HomeworkGraded`), hệ thống tự động gửi thông báo đồng thời qua Discord và Zalo. Nội dung thông báo được định dạng đẹp mắt (Discord Embed với màu sắc nổi bật, Zalo Message) kèm hình ảnh meme học tập từ thư mục assets (`meme-hoc-bai.webp`, `meme-lam-viec.webp`) cùng link trực tiếp đến bài tập.

**Why this priority**: Use case cốt lõi giúp học viên hào hứng, nắm bắt thông tin deadline rõ ràng và xem phản hồi chấm bài ngay lập tức.

**Independent Test**: Kích hoạt giao bài tập mới cho một học viên đã kết nối Discord và Zalo. Kiểm tra tin nhắn được gửi đồng thời đến cả 2 nền tảng với đầy đủ thông tin deadline, link nộp bài và ảnh meme tương ứng.

**Acceptance Scenarios**:

1. **Given** Học viên đã liên kết Discord và Zalo Bot, **When** Giảng viên giao bài tập mới, **Then** hệ thống gửi thông báo chi tiết bài tập kèm ảnh meme học bài (`meme-hoc-bai.webp`) đến cả Discord (Rich Embed) và Zalo Bot.
2. **Given** Bài tập của học viên được chấm điểm và nhận xét, **When** sự kiện `HomeworkGraded` phát ra, **Then** học viên nhận được thông báo điểm số, nhận xét chi tiết kèm meme phù hợp trên cả 2 kênh.

---

### User Story 3 - Nâng cấp thông báo Vi phạm & Điểm thưởng (Violation & Bonus Point) kèm meme cảm xúc (Priority: P1)

Khi học viên bị lập biên bản vi phạm (`ViolationCreated`) hoặc được cộng/trừ điểm thưởng (`BonusPointCreated`), hệ thống gửi thông báo cảnh báo tức thì qua Discord và Zalo kèm meme tương ứng (`meme-doi-no-2.jpg`, `meme-khoc.webp`, `meme-xin-tien.jpeg`) để học viên nắm rõ lý do, số tiền/điểm phạt và thực hiện khắc phục.

**Why this priority**: Tăng tính răn đe nhưng vẫn giữ không khí vui vẻ, thân thiện cho câu lạc bộ qua hình ảnh meme, giúp học viên đối soát điểm và vi phạm kịp thời.

**Independent Test**: Tạo một biên bản vi phạm cho học viên. Kiểm tra thông báo được gửi đến Discord và Zalo của học viên kèm lý do vi phạm và hình ảnh meme nhắc nhở.

**Acceptance Scenarios**:

1. **Given** Học viên bị ghi nhận vi phạm (đi trễ, thiếu bài tập), **When** sự kiện `ViolationCreated` phát ra, **Then** hệ thống gửi thông báo cảnh báo chi tiết kèm ảnh meme (`meme-doi-no-2.jpg` hoặc `meme-khoc.webp`) đến Discord và Zalo của học viên.
2. **Given** Thành viên được thưởng hoặc bị trừ điểm rèn luyện, **When** sự kiện `BonusPointCreated` phát ra, **Then** thành viên nhận được thông báo số điểm biến động và lý do kèm meme (`meme-xin-tien.jpeg` hoặc `meme-ngac-nhien.jpeg`).

---

### User Story 4 - Nâng cấp thông báo Buổi sinh hoạt & Đơn xin phép (Meeting & Permission Request) (Priority: P1)

Khi có buổi sinh hoạt mới được tạo (`MeetingCreated`), cập nhật lịch học (`MeetingUpdated`), hoặc thành viên check-in thành công (`ParticipantCheckedIn`), hệ thống gửi thông báo tới người tham gia kèm meme nhắc nhở (`anh-nhac-em-meme-9.webp`). Khi có đơn xin phép mới (`PermissionRequestCreated`), hệ thống thông báo vào room quản lý kèm chi tiết lý do xin phép.

**Why this priority**: Đảm bảo toàn bộ thành viên nắm rõ lịch sinh hoạt và ban quản lý tiếp nhận các đơn xin nghỉ kịp thời.

**Independent Test**: Tạo một buổi sinh hoạt mới và điểm danh 1 thành viên. Xác minh tin nhắn thông báo được gửi đến người tham gia với đầy đủ tiêu đề, thời gian và meme nhắc nhở.

**Acceptance Scenarios**:

1. **Given** Buổi sinh hoạt mới được lên lịch, **When** sự kiện `MeetingCreated` phát ra, **Then** toàn bộ thành viên trong danh sách tham gia nhận được thông báo lịch học kèm meme nhắc nhở (`anh-nhac-em-meme-9.webp`) trên Discord và Zalo.
2. **Given** Thành viên thực hiện check-in buổi học thành công, **When** sự kiện `ParticipantCheckedIn` phát ra, **Then** thành viên nhận được tin nhắn xác nhận điểm danh thành công trên Discord và Zalo.
3. **Given** Thành viên gửi đơn xin phép nghỉ/trễ, **When** sự kiện `PermissionRequestCreated` phát ra, **Then** ban quản lý nhận được thông báo vào Discord Room kèm thông tin lý do và loại đơn.

---

### Edge Cases

- **Tệp hình ảnh asset cục bộ được phục vụ (Serve static assets)**: Các file meme trong `backend/app/assets` cần có URL công khai (qua StaticFiles mount hoặc CDN/MinIO) để Discord và Zalo có thể tải và hiển thị hình ảnh.
- **Link hình ảnh không khả dụng hoặc lỗi mạng**: Nếu việc tải ảnh gặp sự cố, hệ thống tự động fallback gửi tin nhắn văn bản thuần/embed chuẩn, tuyệt đối không làm gián đoạn việc gửi nội dung thông báo.
- **Tài khoản Discord hoặc Zalo bị mất kết nối / bị chặn (Blocked/Forbidden)**: Khi gửi tin nhắn gặp lỗi 403 Forbidden hoặc người dùng chặn bot, hệ thống ghi log cảnh báo và không làm gián đoạn việc gửi tin qua kênh còn lại.
- **Người dùng chỉ liên kết 1 trong 2 kênh (chỉ Discord hoặc chỉ Zalo)**: Hệ thống bỏ qua kênh chưa liên kết một cách an toàn và gửi bình thường qua kênh hiện có.
- **Sự cố mạng hoặc dịch vụ bên thứ 3 gián đoạn tạm thời**: Tự động áp dụng cơ chế Retry có Exponential Backoff (tối đa 3 lần) cho từng kênh độc lập.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI nâng cấp và chuẩn hóa việc gửi thông báo song song qua hai kênh độc lập: Discord (DM / Embeds) và Zalo Bot (Text / Photo Messages) cho các use case hiện có:
  1. **Billing**: Tạo/Nhắc hóa đơn mới (`InvoiceCreated`), Xác nhận thanh toán thành công (`InvoicePaid`).
  2. **Homework**: Tạo bài tập (`HomeworkAssigned`), Chấm điểm bài tập (`HomeworkGraded`).
  3. **Violation**: Lập biên bản (`ViolationCreated`), Cập nhật vi phạm (`ViolationUpdated`).
  4. **Bonus Point**: Tạo điểm thưởng (`BonusPointCreated`), Cập nhật điểm (`BonusPointUpdated`), Xóa điểm (`BonusPointDeleted`).
  5. **Meeting**: Tạo buổi học (`MeetingCreated`), Cập nhật lịch (`MeetingUpdated`), Điểm danh (`ParticipantCheckedIn`).
  6. **Permission Request**: Gửi đơn xin phép (`PermissionRequestCreated`).
- **FR-002**: Hệ thống PHẢI ánh xạ và tích hợp bộ ảnh meme trong `backend/app/assets` vào các mẫu thông báo theo đúng ngữ cảnh sự kiện:
  - `meme-xin-tien.jpeg` / `meme-doi-no-2.jpg` cho Hóa đơn mới cần thanh toán.
  - `meme-lam-viec-3.jpeg` / `meme-lam-viec-4.jpeg` cho Thanh toán hóa đơn thành công.
  - `meme-hoc-bai.webp` / `meme-lam-viec.webp` cho Homework.
  - `meme-doi-no-2.jpg` / `meme-khoc.webp` cho Violation.
  - `meme-xin-tien.jpeg` / `meme-ngac-nhien.jpeg` cho Bonus Point.
  - `anh-nhac-em-meme-9.webp` / `meme-met-moi-lam-viec.jpg` cho Meeting và Permission Request.
- **FR-003**: Hệ thống PHẢI cung cấp cơ chế truy cập công khai (Static Asset URL) cho các tệp ảnh trong `backend/app/assets` để Discord Embeds và Zalo Photo Messages có thể render trực tiếp.
- **FR-004**: Hệ thống PHẢI xử lý bất đồng bộ (Asynchronous Background Tasks) cho mọi thao tác gửi tin nhắn, không làm chậm luồng xử lý API chính hoặc Webhook xử lý SePay.
- **FR-005**: Hệ thống PHẢI tách biệt hoàn toàn luồng xử lý lỗi của từng kênh (Fault Isolation), có cơ chế Exponential Backoff Retry (tối đa 3 lần) cho mỗi kênh độc lập.
- **FR-006**: Hệ thống PHẢI tự động fallback về tin nhắn văn bản thuần túy nếu hình ảnh meme không tải được hoặc xảy ra sự cố nạp asset.

---

### Key Entities

- **NotificationMessage**: Cấu trúc dữ liệu thông điệp chuẩn hóa (gồm `user_id`, `title`, `content`, `category`, `image_asset_name: str | None`, `image_url: str | None`, `action_url: str | None`).
- **NotificationLog**: Bản ghi nhật ký gửi tin (gồm `id`, `user_id`, `channel` [DISCORD/ZALO], `category`, `status` [SENT/FAILED/SKIPPED], `error_message`, `sent_at`).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% các sự kiện Billing (Hóa đơn mới, Thanh toán thành công qua SePay) và các sự kiện Homework, Violation, Bonus Point, Meeting, Permission Request đều kích hoạt thông báo song song đến cả Discord và Zalo của người dùng liên quan trong vòng dưới 3 giây.
- **SC-002**: 100% các thông báo gửi đi đều hiển thị kèm hình ảnh meme tương ứng từ kho `backend/app/assets` một cách trực quan, đẹp mắt.
- **SC-003**: Cơ chế fallback hoạt động 100% tin cậy: nếu URL ảnh bị lỗi, nội dung tin nhắn vẫn được gửi đến người dùng an toàn.
- **SC-004**: Khi một trong hai nền tảng (Discord hoặc Zalo) gặp sự cố, 100% tin nhắn ở nền tảng còn lại vẫn được chuyển giao thành công mà không gây gián đoạn hệ thống.

---

## Assumptions

- Các use case hiện tại trong backend (bao gồm cả SePay webhook xử lý thanh toán) sẽ phát Domain Events hoặc gọi Asynchronous Handlers để gửi đồng bộ cả Discord và Zalo.
- Thư mục `backend/app/assets` chứa các file meme có sẵn và sẽ được cấu hình static mount qua FastAPI endpoint để sinh URL công khai cho Discord/Zalo.
- Các token `DISCORD_BOT_TOKEN` và `ZALO_BOT_TOKEN` đã được cấu hình trong `Settings`.
