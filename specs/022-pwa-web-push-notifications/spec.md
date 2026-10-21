# Feature Specification: PWA & Web Push Notification System

**Feature Branch**: `022-pwa-web-push-notifications`

**Created**: 2026-10-21

**Status**: Draft

**Input**: User description: "Nếu mục tiêu ưu tiên số 1 là: 'Thông báo nổi bật lên điện thoại như app native mà không tốn phí duy trì Zalo OA': Chuyển bản Web FE hiện tại thành PWA là giải pháp tối ưu nhất. Bạn chỉ cần bổ sung manifest.json, một file sw.js (Service Worker) và tích hợp web-push ở Backend."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cài đặt ứng dụng PWA và Đăng ký nhận Thông báo Đẩy (Priority: P1)

Là một thành viên/sinh viên DUT AI, tôi muốn có thể dễ dàng cài đặt ứng dụng web DUT AI Manager ra màn hình chính điện thoại và kích hoạt nhận thông báo đẩy hệ thống, để tôi nhận được thông báo trực tiếp trên màn hình khóa điện thoại mà không cần phải mở sẵn trình duyệt.

**Why this priority**: Đây là nền tảng cốt lõi của tính năng. Nếu không cài đặt và cấp quyền nhận thông báo đẩy thành công trên thiết bị của người dùng, hệ thống không thể chuyển giao thông báo ra ngoài màn hình khóa giống như ứng dụng native.

**Independent Test**: Người dùng truy cập trang web trên điện thoại (Android hoặc iOS 16.4+), thấy nút "Cài đặt ứng dụng" / hướng dẫn "Thêm vào MH chính", sau đó mở icon từ màn hình chính và bấm "Cho phép nhận thông báo". Thiết bị hiển thị xác nhận đã đăng ký thành công.

**Acceptance Scenarios**:

1. **Given** người dùng truy cập web trên điện thoại Android qua Chrome, **When** hệ thống nhận diện ứng dụng hỗ trợ PWA, **Then** hiển thị banner/nút gợi ý người dùng cài đặt ứng dụng vào màn hình chính chỉ với 1 thao tác.
2. **Given** người dùng truy cập web trên iPhone/iPad qua Safari, **When** người dùng chưa thêm ứng dụng ra màn hình chính, **Then** hiển thị hướng dẫn trực quan (chạm biểu tượng Share -> chọn 'Thêm vào MH chính').
3. **Given** người dùng đã mở ứng dụng từ màn hình chính sau khi đăng nhập, **When** người dùng kích hoạt nhận thông báo, **Then** trình duyệt hiển thị hộp thoại xin cấp quyền hệ thống và lưu thông tin đăng ký thiết bị vào tài khoản người dùng.

---

### User Story 2 - Tự động đẩy thông báo ra màn hình khoá khi có sự kiện (Priority: P1)

Là một thành viên câu lạc bộ, tôi muốn điện thoại của tôi rung chuông và hiển thị thông báo đẩy trên thanh trạng thái / màn hình khóa ngay khi có lịch họp mới, nhắc nhở nộp bài tập sắp đến hạn, hoặc phân công lịch trực nhật, ngay cả khi tôi đã đóng ứng dụng hoặc tắt màn hình điện thoại.

**Why this priority**: Đảm bảo thành viên không bị bỏ lỡ các deadline học tập và buổi sinh hoạt bắt buộc, giải quyết triệt để vấn đề thành viên quên giờ hoặc không check web thường xuyên.

**Independent Test**: Người dùng tắt ứng dụng trên điện thoại; Người quản trị tạo một lịch họp hoặc giao bài tập mới trên hệ thống; Điện thoại của người dùng nhận được thông báo đẩy sau vài giây kèm âm thanh và nội dung tóm tắt.

**Acceptance Scenarios**:

1. **Given** thành viên đã cấp quyền thông báo trên điện thoại và đã đóng ứng dụng, **When** hệ thống tạo lịch sinh hoạt mới có thành viên tham gia, **Then** điện thoại nhận được thông báo đẩy với tiêu đề và tóm tắt thời gian buổi họp.
2. **Given** còn 2 tiếng trước hạn chót nộp bài tập mà thành viên chưa nộp, **When** hệ thống kích hoạt tiến trình nhắc nhở tự động, **Then** điện thoại của thành viên hiển thị thông báo cảnh báo hạn chót nộp bài.
3. **Given** thành viên đăng nhập trên nhiều thiết bị (điện thoại và máy tính), **When** có thông báo mới gửi đến tài khoản, **Then** cả hai thiết bị đều nhận được thông báo đẩy đồng thời.

---

### User Story 3 - Chạm vào thông báo để mở thẳng trang nội dung chi tiết (Priority: P2)

Là một thành viên, khi nhận được thông báo đẩy trên điện thoại, tôi muốn chạm vào thông báo để mở ứng dụng và điều hướng tức thì đến đúng trang chi tiết của sự kiện đó (ví dụ: mở thẳng bài tập cần nộp hoặc chi tiết buổi họp), thay vì phải tự tìm kiếm từ trang chủ.

**Why this priority**: Cải thiện đáng kể trải nghiệm người dùng (UX), giảm số thao tác từ 4-5 bước xuống còn 1 chạm để hoàn thành nhiệm vụ (nộp bài, xác nhận điểm danh).

**Independent Test**: Gửi một thông báo đẩy về bài tập lab cụ thể; người dùng chạm vào thông báo trên thanh thông báo điện thoại; ứng dụng mở ra và hiển thị trực tiếp trang nộp bài của bài tập đó.

**Acceptance Scenarios**:

1. **Given** điện thoại đang hiển thị thông báo về "Buổi sinh hoạt tuần 8", **When** người dùng chạm vào thông báo, **Then** ứng dụng mở lên và tự động chuyển đến màn hình chi tiết buổi họp tuần 8.
2. **Given** điện thoại đang hiển thị thông báo nhắc nộp bài tập lab, **When** người dùng chạm vào thông báo, **Then** ứng dụng mở lên và đưa người dùng vào ngay form nộp bài tập tương ứng.

---

### Edge Cases

- **Người dùng từ chối cấp quyền thông báo (Permission Denied)**:
  - Khi trình duyệt báo trạng thái bị chặn (Denied), ứng dụng không thể tiếp tục hiển thị prompt xin quyền của hệ điều hành. Hệ thống cần hiển thị thông báo hướng dẫn người dùng cách mở lại quyền trong phần Cài đặt trình duyệt/Cài đặt thiết bị nếu họ muốn bật lại sau này.
- **Thiết bị ngoại tuyến (Offline) khi hệ thống gửi thông báo**:
  - Dịch vụ đẩy thông báo tiêu chuẩn (Push Service) sẽ lưu thông báo vào hàng đợi tạm thời và tự động phân phát xuống thiết bị ngay khi thiết bị có kết nối mạng Internet trở lại.
- **Token thiết bị hết hạn hoặc không còn hợp lệ (Stale / Unsubscribed)**:
  - Khi người dùng gỡ cài đặt PWA hoặc xoá dữ liệu trình duyệt, Push Service sẽ phản hồi mã trạng thái không hợp lệ. Hệ thống máy chủ phải tự động dọn dẹp các bản ghi đăng ký hết hạn này khỏi cơ sở dữ liệu để tránh lãng phí tài nguyên.
- **Hạn chế của iOS dưới phiên bản 16.4**:
  - Các thiết bị iOS chạy phiên bản cũ hơn 16.4 không hỗ trợ Web Push Notification. Hệ thống cần phát hiện và thông báo nhẹ nhàng cho người dùng biết cần nâng cấp hệ điều hành hoặc sử dụng hòm thư thông báo nội bộ (In-App Inbox).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống MUST cung cấp tệp cấu hình ứng dụng web tiến bộ (Web App Manifest) với đầy đủ định danh, tên hiển thị, màu sắc chủ đạo, chế độ toàn màn hình (`standalone`) và bộ biểu tượng (icons) chuẩn hoá cho các kích cỡ màn hình khác nhau.
- **FR-002**: Ứng dụng web MUST đăng ký tiến trình chạy nền (Service Worker) để duy trì khả năng nhận và hiển thị thông báo đẩy khi ứng dụng không hoạt động trên màn hình.
- **FR-003**: Ứng dụng MUST cung cấp giao diện trực quan hướng dẫn người dùng cài đặt ứng dụng vào màn hình chính phù hợp theo từng loại hệ điều hành (Android hiển thị banner cài đặt trực tiếp, iOS hiển thị hướng dẫn chia sẻ Safari).
- **FR-004**: Ứng dụng MUST hỗ trợ quy trình xin cấp quyền nhận thông báo từ người dùng và đăng ký kênh thông báo đẩy (Push Subscription) an toàn theo chuẩn định danh máy chủ (VAPID).
- **FR-005**: Hệ thống máy chủ MUST lưu trữ thông tin đăng ký thiết bị (Push Subscription endpoint, khoá mã hoá xác thực) gắn liền với tài khoản người dùng đang đăng nhập.
- **FR-006**: Khi phát sinh các sự kiện nghiệp vụ quan trọng (phân công lịch họp, nhắc nộp bài tập, phân công trực nhật), hệ thống máy chủ MUST tự động tạo và gửi tải trọng thông báo (payload gồm tiêu đề, nội dung tóm tắt, icon, và đường dẫn điều hướng) tới các thiết bị đang hoạt động của người dùng liên quan.
- **FR-007**: Tiến trình nền trên thiết bị người dùng MUST tiếp nhận sự kiện đẩy và hiển thị thẻ thông báo hệ thống kèm rung/âm thanh và huy hiệu ứng dụng (nếu hệ điều hành hỗ trợ).
- **FR-008**: Khi người dùng chạm vào thẻ thông báo, hệ thống MUST tự động mở ứng dụng và điều hướng trực tiếp tới đúng trang dữ liệu tương ứng được chỉ định trong thông báo.
- **FR-009**: Hệ thống máy chủ MUST tự động phát hiện và vô hiệu hoá các token thiết bị đã hết hạn hoặc không còn tồn tại khi gửi thông báo thất bại.

---

### Key Entities

- **Push Subscription (Đăng ký thiết bị)**:
  - Đại diện cho một kênh kết nối thông báo đẩy của một trình duyệt/thiết bị cụ thể của người dùng.
  - Thuộc tính chính: Mã định danh người dùng (`user_id`), Địa chỉ điểm cuối (`endpoint`), Khoá công khai mã hoá (`p256dh`), Khoá xác thực bí mật (`auth`), Thông tin thiết bị/trình duyệt (`user_agent`), Thời điểm đăng ký lần cuối, Trạng thái kích hoạt.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% người dùng trên Android và iOS (từ phiên bản 16.4 trở lên) có thể thêm ứng dụng ra màn hình chính và nhận được thông báo đẩy ra màn hình khoá thiết bị mà không cần mở sẵn trình duyệt.
- **SC-002**: Thời gian từ lúc hệ thống máy chủ phát lệnh gửi thông báo đẩy đến lúc thiết bị người dùng rung/hiển thị thông báo đạt dưới 5 giây trong điều kiện mạng thông thường.
- **SC-003**: 95% thao tác chạm vào thông báo mở ứng dụng và đưa người dùng đến đúng trang nội dung chi tiết trong vòng dưới 2 giây.
- **SC-004**: Tỷ lệ thành viên nộp bài tập trễ hạn giảm tối thiểu 30% sau 1 tháng áp dụng cơ chế nhắc nhở đẩy tự động qua PWA.
- **SC-005**: Chi phí vận hành thông báo đẩy qua hạ tầng Web Push là 0 VNĐ (hoàn toàn miễn phí, độc lập với các dịch vụ trả phí bên ngoài).

---

## Assumptions

- Thiết bị của người dùng có kết nối mạng Internet (Wi-Fi hoặc 4G/5G) để nhận thông báo đẩy từ các dịch vụ máy chủ thông báo của Google (FCM) hoặc Apple (APNs).
- Người dùng iOS sử dụng hệ điều hành iOS 16.4 trở lên (phiên bản Apple bắt đầu hỗ trợ chuẩn Web Push cho ứng dụng thêm vào màn hình chính).
- Ứng dụng web được phục vụ qua giao thức mã hoá an toàn HTTPS (yêu cầu bảo mật bắt buộc của chuẩn Service Worker và Web Push trên tất cả các trình duyệt hiện đại).
- Tận dụng hệ thống xác thực người dùng và dữ liệu thông báo sẵn có của hệ thống DUT AI Manager hiện tại.
