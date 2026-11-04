# Feature Specification: Tự Động Làm Mới Token Khi Hết Hạn (Auto Refresh Token)

**Feature Branch**: `049-auto-refresh-token`

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: "Hiện tại hệ thống web của tôi chưa có tính năng tựng sử dụng refresh token khi access_token hết hạn, dẫn đến hệ thống tự động đăng xuất mỗi khi access_token hết hạn => Hãy thêm chức năng vào hệ thống giúp tôi"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tự động gia hạn phiên làm việc ngầm khi Access Token hết hạn (Priority: P1)

Là một người dùng đang sử dụng hệ thống web (ví dụ: quản lý cuộc họp, nộp bài tập, xem báo cáo), khi phiên làm việc ngắn hạn (access token) của tôi hết hạn trong lúc tôi đang xem hoặc thực hiện thao tác, tôi muốn hệ thống tự động làm mới phiên làm việc ngầm và thực hiện thao tác của tôi mà không bị gián đoạn hay bị văng ra màn hình đăng nhập.

**Why this priority**: Đây là giá trị cốt lõi giải quyết trực tiếp vấn đề người dùng bị tự động đăng xuất phi lý khi đang làm việc, bảo đảm tính liên tục và trải nghiệm mượt mà không bị ngắt quãng.

**Independent Test**: Đăng nhập vào hệ thống, đợi hoặc thiết lập cho access token hết hạn, thực hiện một thao tác gửi yêu cầu dữ liệu (như xem danh sách người tham gia cuộc họp). Thao tác vẫn hoàn thành thành công, dữ liệu hiển thị bình thường, và người dùng không phải đăng nhập lại.

**Acceptance Scenarios**:

1. **Given** người dùng đã đăng nhập và access token đã hết hạn nhưng refresh token vẫn còn hiệu lực, **When** người dùng thực hiện một thao tác gửi yêu cầu dữ liệu lên hệ thống, **Then** hệ thống tự động kích hoạt làm mới phiên làm việc ngầm, thực thi lại yêu cầu ban đầu thành công và hiển thị kết quả cho người dùng mà không có thông báo lỗi phiên hết hạn.
2. **Given** người dùng đã đăng nhập và access token hết hạn trong thời gian không thao tác, **When** người dùng quay lại và truy cập vào trang chủ hoặc bất kỳ trang tính năng nào, **Then** hệ thống ngầm cấp mới access token và duy trì trạng thái đăng nhập của người dùng thay vì điều hướng về màn hình đăng nhập.

---

### User Story 2 - Xếp hàng và thực thi lại các yêu cầu đồng thời trong quá trình làm mới phiên (Priority: P2)

Là một người dùng đang tải một trang tổng hợp có nhiều biểu đồ, danh sách và tác vụ ngầm chạy cùng một lúc, khi access token hết hạn, tôi muốn tất cả các yêu cầu đang gửi đồng thời đều được xếp hàng xử lý an toàn và chỉ kích hoạt duy nhất một lượt làm mới phiên, sau đó tất cả các yêu cầu đều nhận được kết quả chính xác mà không gặp lỗi từ chối phiên cục bộ.

**Why this priority**: Trong ứng dụng web hiện đại, một màn hình thường kích hoạt nhiều yêu cầu dữ liệu song song. Nếu không có cơ chế xếp hàng đồng bộ, nhiều yêu cầu sẽ kích hoạt hàng loạt yêu cầu làm mới trùng lặp, gây xung đột và làm hỏng phiên làm việc.

**Independent Test**: Kích hoạt đồng thời 5-10 yêu cầu dữ liệu khi access token vừa hết hạn. Hệ thống chỉ phát đi duy nhất một yêu cầu làm mới phiên, sau đó cả 5-10 yêu cầu đều được giải phóng và hoàn thành thành công với dữ liệu chuẩn xác.

**Acceptance Scenarios**:

1. **Given** access token vừa hết hạn và có nhiều yêu cầu dữ liệu được gửi đi cùng một thời điểm, **When** yêu cầu đầu tiên nhận tín hiệu phiên hết hạn và bắt đầu tiến trình làm mới, **Then** các yêu cầu tiếp theo được tự động đưa vào hàng đợi chờ và không kích hoạt thêm yêu cầu làm mới phiên thứ hai.
2. **Given** các yêu cầu đang nằm trong hàng đợi chờ làm mới phiên, **When** tiến trình làm mới phiên thành công, **Then** toàn bộ các yêu cầu trong hàng đợi được tự động gửi lại với phiên mới và trả kết quả về cho từng thành phần giao diện tương ứng.

---

### User Story 3 - Xử lý đăng xuất an toàn khi Refresh Token hết hạn hoặc không hợp lệ (Priority: P3)

Là một người dùng không sử dụng hệ thống trong thời gian dài (vượt quá thời hạn của cả refresh token) hoặc phiên làm việc đã bị hủy từ máy chủ, khi tôi truy cập lại hoặc gửi yêu cầu, tôi muốn nhận được thông báo rõ ràng rằng phiên đăng nhập đã hết hạn và được chuyển hướng an toàn về màn hình đăng nhập để xác thực lại.

**Why this priority**: Đảm bảo an toàn bảo mật khi phiên thực sự đã kết thúc, đồng thời cung cấp phản hồi minh bạch, tránh tình trạng giao diện bị treo hoặc rơi vào vòng lặp tải trang vô tận.

**Independent Test**: Sử dụng tài khoản có cả access token và refresh token đã hết hạn (hoặc bị vô hiệu hóa trên máy chủ), thực hiện một thao tác trên giao diện. Hệ thống dừng các yêu cầu tiếp theo, hiển thị thông báo "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại" và chuyển người dùng về màn hình đăng nhập một cách mượt mà.

**Acceptance Scenarios**:

1. **Given** cả access token và refresh token đều đã hết hạn hoặc không hợp lệ, **When** hệ thống thực hiện làm mới phiên và nhận phản hồi từ chối từ máy chủ, **Then** hệ thống xóa sạch trạng thái xác thực cục bộ, dừng các yêu cầu trong hàng đợi, hiển thị thông báo rõ ràng cho người dùng và chuyển hướng đến trang đăng nhập.
2. **Given** người dùng đang ở tại màn hình đăng nhập, **When** có lỗi xác thực xảy ra, **Then** hệ thống không kích hoạt tiến trình làm mới phiên tự động để tránh lặp vô tận.

---

### Edge Cases

- **Khi refresh token bị thu hồi hoặc mất hiệu lực đột ngột**: Tiến trình làm mới phiên thất bại ngay lập tức, toàn bộ hàng đợi yêu cầu bị hủy bỏ với thông báo lỗi phù hợp và chuyển hướng người dùng về trang đăng nhập mà không lặp lại yêu cầu làm mới.
- **Khi mạng internet bị ngắt kết nối trong lúc đang làm mới phiên**: Hệ thống giữ trạng thái lỗi kết nối mạng thay vì vội vã kết luận phiên làm việc hết hạn và không tự ý đăng xuất người dùng nếu chưa có phản hồi dứt khoát từ máy chủ.
- **Khi người dùng mở nhiều tab trình duyệt cùng một lúc**: Cơ chế làm mới token hoạt động đồng bộ, chia sẻ trạng thái phiên mới giữa các tab để không tab nào bị rơi vào trạng thái đăng xuất ngoài ý muốn.
- **Khi người dùng chủ động chọn "Đăng xuất"**: Toàn bộ phiên làm việc (cả access token và refresh token) bị hủy bỏ ngay lập tức, hàng đợi được làm trống và chuyển hướng về màn hình đăng nhập.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI có khả năng phát hiện tự động khi phiên làm việc ngắn hạn (access token) bị hết hạn hoặc không hợp lệ thông qua mã phản hồi từ chối xác thực từ máy chủ.
- **FR-002**: Khi phát hiện access token hết hạn, hệ thống PHẢI tự động kích hoạt tiến trình làm mới phiên ngầm (silent token refresh) bằng refresh token mà không làm gián đoạn tác vụ của người dùng.
- **FR-003**: Hệ thống PHẢI tạm dừng và lưu trữ yêu cầu ban đầu bị từ chối, sau đó tự động phát lại (retry) yêu cầu đó ngay sau khi phiên làm việc được làm mới thành công.
- **FR-004**: Hệ thống PHẢI duy trì cờ trạng thái làm mới tập trung (single refresh state) để đảm bảo chỉ có duy nhất một tiến trình làm mới phiên được thực thi tại một thời điểm.
- **FR-005**: Hệ thống PHẢI duy trì hàng đợi (pending request queue) chứa tất cả các yêu cầu phát sinh đồng thời trong lúc tiến trình làm mới phiên đang chạy, và tự động giải phóng hàng đợi khi tiến trình làm mới hoàn thành.
- **FR-006**: Khi tiến trình làm mới phiên thất bại (do refresh token hết hạn, không hợp lệ, hoặc bị thu hồi), hệ thống PHẢI dừng toàn bộ hàng đợi, dọn dẹp trạng thái xác thực người dùng, hiển thị thông báo phiên đã hết hạn và chuyển hướng người dùng về màn hình đăng nhập.
- **FR-007**: Hệ thống PHẢI loại trừ các yêu cầu thuộc trang đăng nhập hoặc yêu cầu làm mới chính nó khỏi tiến trình thử lại tự động để ngăn chặn vòng lặp vô tận (infinite retry loop).
- **FR-008**: Khi người dùng tải lại trang hoặc mở trang chủ với phiên ngắn hạn đã hết hạn nhưng phiên dài hạn còn hiệu lực, hệ thống PHẢI tự động cấp mới phiên và tải thông tin người dùng thành công thay vì chuyển hướng ngay sang màn hình đăng nhập.

### Key Entities

- **User Session**: Đại diện cho phiên xác thực của người dùng trong hệ thống, bao gồm định danh người dùng, trạng thái đăng nhập (đã xác thực / chưa xác thực), thông tin phiên ngắn hạn (access token) và thông tin phiên dài hạn (refresh token).
- **Session Refresh Manager**: Bộ điều phối chịu trách nhiệm quản lý vòng đời làm mới phiên, kiểm soát cờ đang làm mới (refreshing flag), quản lý hàng đợi các yêu cầu đang chờ giải phóng (pending requests queue), và xử lý quyết định tiếp tục phiên hay điều hướng đăng xuất.
- **Queued Request**: Đại diện cho một yêu cầu nghiệp vụ bị tạm giữ khi access token hết hạn, chứa đầy đủ thông tin ngữ cảnh ban đầu để có thể thực thi lại chính xác sau khi phiên mới sẵn sàng.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% các thao tác nghiệp vụ của người dùng khi access token hết hạn (trong điều kiện refresh token còn hạn) được thực thi thành công mà không yêu cầu người dùng đăng nhập lại hoặc tải lại trang.
- **SC-002**: Tỷ lệ người dùng bị đăng xuất bất thường khi đang thao tác liên tục giảm về 0%.
- **SC-003**: 100% các yêu cầu đồng thời phát sinh trong thời gian làm mới phiên được thực thi lại thành công và đúng dữ liệu mục tiêu.
- **SC-004**: Thời gian hoàn tất việc làm mới phiên ngầm và gửi lại yêu cầu bị gián đoạn diễn ra dưới 1.5 giây trong điều kiện mạng bình thường, không gây cảm giác đơ giật giao diện.
- **SC-005**: Khi refresh token hết hạn hoàn toàn, hệ thống thực hiện chuyển hướng người dùng về màn hình đăng nhập chính xác trong đúng 1 lần thử duy nhất, không xuất hiện hiện tượng giật lặp màn hình hoặc kẹt hàng đợi.

## Assumptions

- Máy chủ ứng dụng đã hỗ trợ điểm tiếp nhận làm mới phiên hợp lệ và trả về cặp token mới hoặc thiết lập lại cookie phiên tương ứng.
- Thời hạn hiệu lực của refresh token dài hơn đáng kể so với access token (ví dụ: access token tính theo phút/giờ/ngày, refresh token tính theo tuần) để đảm bảo tính hữu dụng của tính năng làm mới ngầm.
- Thiết bị và trình duyệt của người dùng cho phép lưu trữ và truyền nhận thông tin phiên xác thực an toàn theo tiêu chuẩn web hiện đại.
- Khi người dùng chủ động đăng xuất, hệ thống sẽ xóa toàn bộ phiên xác thực và không kích hoạt cơ chế tự động làm mới ngầm.
