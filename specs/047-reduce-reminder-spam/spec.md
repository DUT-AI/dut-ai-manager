# Feature Specification: Tái cấu trúc Nghiệp vụ Nhắc nhở Theo Mốc Đếm Ngược & Loại bỏ Spam Thông báo

**Feature Branch**: `047-reduce-reminder-spam`

**Created**: 2026-11-04

**Status**: Ready for Planning

**Input**: User description: "Hiện tại hệ thống scan nhắn thông báo bị khách hàng nhắn nhỡ spam thông báo nhiều quá hãy suy nghĩ lại nghiệp vụ nhắc nhở để giảm thông báo lại + Bỏ zalobot, chỉ không thông báo báo zalobot nữa, chứ đừng xóa code nhé"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Thành viên chỉ nhận thông báo nhắc nhở theo các mốc đếm ngược hợp lý (24h, 4h, 1h) (Priority: P1) 🎯 Core Value

Là một thành viên tham gia hệ thống, tôi muốn hệ thống chỉ gửi thông báo nhắc việc khi nhiệm vụ của tôi thực sự bước vào các mốc đếm ngược quan trọng (còn 24 giờ, 4 giờ và 1 giờ trước hạn chót), thay vì liên tục bị réo chuông vào các khung giờ cố định trong ngày, để tôi tập trung làm việc và không bị cảm giác bị spam thông báo làm phiền.

**Why this priority**: Việc loại bỏ toàn bộ 4 khung giờ cố định (`08:00`, `12:00`, `19:30`, `22:00`) và chuyển sang 3 mốc đếm ngược chuẩn (`24h`, `4h`, `1h`) loại bỏ ngay lập tức 70-80% số lượng thông báo trùng lặp và dư thừa mỗi ngày.

**Independent Test**:
- Tạo một nhiệm vụ có hạn chót sau 3 ngày (72 giờ).
- Để tiến trình quét chạy qua các khung giờ `08:00`, `12:00`, `19:30`, `22:00`: Xác minh hệ thống KHÔNG gửi bất kỳ thông báo nào vào các giờ này.
- Khi thời gian tiến đến mốc còn 24 giờ trước hạn: Hệ thống gửi đúng 01 thông báo nhắc sớm.
- Khi còn 4 giờ trước hạn: Hệ thống gửi đúng 01 thông báo cảnh báo.
- Khi còn 1 giờ trước hạn: Hệ thống gửi đúng 01 thông báo khẩn cấp.

**Acceptance Scenarios**:
1. **Given** một nhiệm vụ có hạn chót còn trên 24 giờ, **When** hệ thống quét định kỳ, **Then** hệ thống không gửi thông báo lặp lại nhiều lần trong ngày, chỉ ghi nhận nhắc nhở tối đa 1 lần mỗi ngày cho đến khi chạm mốc 24 giờ.
2. **Given** nhiệm vụ bước vào khoảng 24 giờ trước hạn chót, **When** hệ thống quét, **Then** thành viên nhận được đúng 01 thông báo nhắc nhở mốc 24h.
3. **Given** nhiệm vụ bước vào khoảng 4 giờ trước hạn chót, **When** hệ thống quét, **Then** thành viên nhận được đúng 01 thông báo cảnh báo mức độ cao (Warning) mốc 4h.
4. **Given** nhiệm vụ bước vào khoảng 1 giờ trước hạn chót, **When** hệ thống quét, **Then** thành viên nhận được đúng 01 thông báo cảnh báo nguy cấp (Critical) mốc 1h.
5. **Given** thành viên đã nhận thông báo của một mốc đếm ngược cụ thể (ví dụ mốc 24h), **When** các lần quét tiếp theo diễn ra trong cùng khoảng thời gian đó, **Then** hệ thống chặn hoàn toàn việc gửi lại (Deduplication tuyệt đối).

---

### User Story 2 - Loại bỏ hoàn toàn các khung giờ nhắc cố định gây phiền toái và tôn trọng giờ nghỉ ngơi (Priority: P1)

Là một người dùng hệ thống, tôi muốn không còn bị bot réo chuông vào giờ ăn trưa (12:00) hoặc đêm muộn (22:00) theo lịch cố định cũ, để tôi có không gian nghỉ ngơi thoải mái mà không bị đánh thức hoặc gián đoạn sinh hoạt cá nhân.

**Why this priority**: Khung giờ cố định cũ (đặc biệt là 22:00 và 12:00) là nguyên nhân gây ức chế nhất cho khách hàng vì vừa trùng lặp thông tin vừa rơi vào khung giờ nhạy cảm.

**Independent Test**:
- Kiểm tra toàn bộ tiến trình quét lịch biểu của hệ thống: Xác minh các mốc giờ cố định `FIXED_0800`, `FIXED_1200`, `FIXED_1930`, `FIXED_2200` đã được gỡ bỏ hoàn toàn khỏi nghiệp vụ quét nhắc việc.
- Quan sát hoạt động thông báo vào lúc 12:00 và 22:00: Hệ thống không tự động phát sinh thông báo trừ khi đúng thời điểm đó có một nhiệm vụ chạm mốc đếm ngược khẩn cấp.

**Acceptance Scenarios**:
1. **Given** thời điểm hiện tại là các mốc giờ cố định cũ (08:00, 12:00, 19:30, 22:00), **When** tiến trình quét chạy, **Then** hệ thống không tự động kích hoạt thông báo cố định cho tất cả các task tồn đọng như trước.
2. **Given** một nhiệm vụ không rơi vào các mốc đếm ngược (24h, 4h, 1h), **When** thời gian trôi qua trong ngày, **Then** nhiệm vụ đó không bị phát thông báo làm phiền lặp đi lặp lại.

---

### User Story 3 - Tạm dừng gửi tin qua kênh Zalo Bot để giảm bớt kênh làm phiền (Priority: P2) 🎯 Multi-Channel Tuning

Là một người dùng hệ thống, tôi muốn không còn nhận tin nhắn spam đẩy qua ứng dụng Zalo từ Zalo Bot nữa, để tin nhắn Zalo cá nhân của tôi không bị quá tải bởi các thông báo tự động của hệ thống, trong khi mã nguồn tích hợp vẫn được giữ nguyên để có thể bật lại trong tương lai khi cần.

**Why this priority**: Cắt giảm kênh Zalo Bot giúp giảm ngay một kênh làm phiền trực tiếp trên điện thoại của học viên, người dùng chỉ nhận qua Discord Bot DM, Web Push và xem trên Web In-App.

**Independent Test**:
- Tạo thông báo hoặc kích hoạt quét nhắc việc cho một người dùng đã liên kết `zalo_bot_id`.
- Xác minh rằng hệ thống gửi thành công lên In-App DB, Discord DM và Web Push, nhưng KHÔNG gửi tin nhắn đến Zalo Bot.
- Kiểm tra mã nguồn: module `ZaloBotClient` và `ZaloNotificationChannel` vẫn được bảo toàn nguyên vẹn, không bị xóa.

**Acceptance Scenarios**:
1. **Given** hệ thống phát thông báo (nhắc nhở hoặc sự kiện), **When** tiến trình điều phối đa kênh chạy, **Then** hệ thống bỏ qua việc gửi tin nhắn qua kênh Zalo Bot.
2. **Given** người dùng có tài khoản Zalo liên kết, **When** nhận thông báo, **Then** người dùng chỉ nhận trên Discord DM, Web Push và xem trên giao diện Web In-App.

---

### User Story 4 - Giữ nguyên định dạng thông báo quen thuộc của từng nhiệm vụ (Priority: P2)

Là một thành viên đã quen thuộc với giao diện thông báo của hệ thống, tôi muốn nội dung thông báo cho từng nhiệm vụ (Bài tập, Trực nhật, Đánh giá cuộc họp) được giữ nguyên phong cách trực quan, đầy đủ thông tin và đường dẫn hành động như hiện tại, nhưng với tần suất được kiểm soát chặt chẽ.

**Why this priority**: Đáp ứng yêu cầu giữ nguyên nghiệp vụ định dạng và quy trình gửi quen thuộc của người dùng, không làm xáo trộn trải nghiệm tiếp nhận thông tin hay cấu trúc hiển thị hiện hành.

**Independent Test**:
- Kích hoạt thông báo mốc 24h hoặc 4h cho 1 bài tập.
- Xác minh rằng thông báo vẫn hiển thị đầy đủ tên bài tập, thời hạn chót chuẩn giờ Việt Nam, thời gian đếm ngược còn lại và đường link dẫn thẳng tới trang nộp bài tập như trước đây.

**Acceptance Scenarios**:
1. **Given** một nhiệm vụ chạm mốc nhắc nhở hợp lệ (24h, 4h hoặc 1h), **When** hệ thống phát thông báo, **Then** thông báo được chuyển tiếp đến các kênh hoạt động (In-App DB, Discord DM, Web Push) với cấu trúc nội dung chuẩn xác như hiện tại.
2. **Given** thông báo được gửi thành công, **When** người dùng mở trang Quản lý Thông báo trên Web (`/dashboard/notifications`), **Then** thông báo hiển thị đầy đủ với huy hiệu trạng thái chưa đọc và liên kết hành động chính xác.

---

### User Story 5 - Tự động loại trừ nhiệm vụ đã hoàn thành hoặc đã được miễn trừ (Priority: P3)

Là một thành viên, khi tôi đã hoàn thành nhiệm vụ (nộp bài tập, nộp ảnh minh chứng trực nhật, hoàn tất đánh giá cuộc họp) hoặc đã được phê duyệt đơn xin vắng/hoãn, tôi muốn hệ thống lập tức ngừng gửi bất kỳ thông báo nhắc nhở nào ở các mốc đếm ngược tiếp theo của nhiệm vụ đó.

**Why this priority**: Đảm bảo tính chính xác tuyệt đối, tránh tình trạng "báo động giả" khiến người dùng mất lòng tin vào hệ thống.

**Independent Test**:
- Thành viên nộp bài tập khi còn 10 giờ trước hạn (đã nhận mốc 24h).
- Đến mốc 4 giờ và 1 giờ trước hạn: Hệ thống quét kiểm tra.
- Xác minh hệ thống không gửi thêm bất kỳ thông báo nào cho mốc 4h và 1h của bài tập đã nộp.

**Acceptance Scenarios**:
1. **Given** thành viên đã nộp bài hoặc hoàn thành nhiệm vụ, **When** nhiệm vụ bước vào mốc đếm ngược tiếp theo (4h hoặc 1h), **Then** hệ thống bỏ qua nhiệm vụ đó và không gửi bất kỳ thông báo nào.
2. **Given** thành viên đã có đơn xin phép vắng hoặc hoãn nhiệm vụ được phê duyệt, **When** hệ thống quét mốc đếm ngược, **Then** hệ thống loại trừ thành viên khỏi danh sách cần nhắc nhở.

---

### Edge Cases

- **Nhiệm vụ được tạo gấp (thời gian từ lúc tạo đến deadline dưới 24h, ví dụ 5h)**: Bỏ qua mốc 24h, chỉ kích hoạt mốc 4h và mốc 1h khi chạm ngưỡng.
- **Nhiệm vụ được tạo cực gấp (dưới 1h)**: Chỉ kích hoạt duy nhất mốc 1h khẩn cấp.
- **Khoảng thời gian quét (Scheduler Interval)**: Vì hệ thống quét định kỳ (mỗi 30 phút một lần), các khoảng thời gian đếm ngược phải có độ bao phủ phù hợp (dung sai hợp lý xung quanh các mốc 24h, 4h, 1h) để đảm bảo không bị bỏ sót mốc nào khi chạy giữa các chu kỳ.
- **Deduplication giữa các chu kỳ quét**: Đảm bảo mỗi mốc đếm ngược (24h, 4h, 1h) chỉ ghi nhận và gửi duy nhất 1 lần cho mỗi cặp `(task_type, task_id, user_id)`.
- **Bảo toàn mã nguồn Zalo Bot**: Toàn bộ codebase hiện tại liên quan đến Zalo Bot Client và Zalo Channel không bị xóa bỏ; cơ chế ngưng gửi được thực hiện thông qua việc tắt kích hoạt kênh (bypass/disabled toggle) tại tầng điều phối để dễ dàng khôi phục khi cần.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI loại bỏ hoàn toàn các khung giờ nhắc nhở cố định trong ngày (`FIXED_0800`, `FIXED_1200`, `FIXED_1930`, `FIXED_2200`).
- **FR-002**: Hệ thống PHẢI chuyển đổi cơ chế kích hoạt nhắc nhở sang thuần túy dựa trên **3 mốc đếm ngược theo hạn chót (Countdown Offsets)**:
  - **Mốc 24 giờ (`OFFSET_1D`)**: Nhắc nhở cảnh báo sớm khi thời gian còn lại đến hạn chót xấp xỉ 24 giờ (khoảng 22h - 26h trước deadline). Đối với các nhiệm vụ còn hạn trên 24 giờ, hệ thống chỉ nhắc tối đa 1 lần mỗi ngày.
  - **Mốc 4 giờ (`OFFSET_4H`)**: Nhắc nhở cảnh báo mức độ cao (khoảng 3.5h - 4.5h trước deadline).
  - **Mốc 1 giờ (`OFFSET_1H`)**: Nhắc nhở cảnh báo nguy cấp cuối cùng (khoảng 0.5h - 1.5h trước deadline).
- **FR-003**: Hệ thống PHẢI loại bỏ các mốc đếm ngược dày đặc không cần thiết khác (loại bỏ mốc `OFFSET_2D` 48 giờ và mốc `OFFSET_12H` 12 giờ) để tinh gọn chu kỳ nhắc nhở.
- **FR-004**: Hệ thống PHẢI ngừng việc gửi thông báo qua kênh Zalo Bot (Mute/Bypass Zalo Bot notification) trong bộ điều phối phát thông báo (`UnifiedNotificationDispatcher`), tuyệt đối KHÔNG xóa mã nguồn của Zalo Bot và Zalo Channel.
- **FR-005**: Các kênh phân phối thông báo hoạt động chính thức gồm: In-App Database (trên trang Web), Discord Bot DM, và Web Push (Trình duyệt).
- **FR-006**: Hệ thống PHẢI giữ nguyên định dạng nội dung thông báo cho từng nhiệm vụ đơn lẻ theo đúng nghiệp vụ và mẫu hiển thị đã được người dùng phê chuẩn.
- **FR-007**: Hệ thống PHẢI đảm bảo tính chống trùng lặp tuyệt đối (Deduplication): Mỗi mốc đếm ngược (`OFFSET_1D`, `OFFSET_4H`, `OFFSET_1H`) chỉ gửi đúng 01 lần duy nhất cho mỗi nhiệm vụ cụ thể của từng thành viên.
- **FR-008**: Hệ thống PHẢI kiểm tra trạng thái hoàn thành nhiệm vụ thời gian thực tại thời điểm quét: Bỏ qua ngay lập tức các nhiệm vụ mà thành viên đã nộp bài, đã nộp minh chứng hoặc đã có đơn xin hoãn/vắng được duyệt.
- **FR-009**: Hệ thống PHẢI duy trì việc lưu trữ lịch sử thông báo đầy đủ trong cơ sở dữ liệu để hiển thị trên trang Quản lý Thông báo (`/dashboard/notifications`) với phân trang và bộ lọc chuẩn mực.

### Key Entities *(include if feature involves data)*

- **Mốc Nhắc nhở Đếm ngược (Reminder Countdown Stage)**: Giá trị đại diện cho các mốc thời gian trước hạn chót được kích hoạt nhắc việc, bao gồm chính xác 3 mốc: `OFFSET_1D` (24 giờ trước hạn), `OFFSET_4H` (4 giờ trước hạn), và `OFFSET_1H` (1 giờ trước hạn).
- **Thông báo Nhắc việc (Task Reminder Notification)**: Đại diện cho một thông điệp nhắc việc cụ thể gắn liền với một công việc, một người nhận, một mốc đếm ngược và trạng thái phát qua các kênh thông tin đang hoạt động.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Giảm ít nhất 70% tổng số lượng thông báo nhắc việc phát sinh mỗi ngày so với cơ chế cũ (nhờ loại bỏ hoàn toàn 4 khung giờ cố định và 2 mốc đếm ngược thừa).
- **SC-002**: Mỗi nhiệm vụ chưa hoàn thành chỉ phát sinh tối đa đúng 3 thông báo trong suốt vòng đời của nó (tương ứng với 3 mốc: 24h, 4h, 1h).
- **SC-003**: 0 thông báo được gửi vào các khung giờ cố định cũ (08:00, 12:00, 19:30, 22:00) nếu nhiệm vụ không chạm đúng mốc đếm ngược.
- **SC-004**: 0 tin nhắn thông báo được gửi qua kênh Zalo Bot sau khi áp dụng cấu hình ngưng phát thông báo Zalo.
- **SC-005**: 100% mã nguồn Zalo Bot và Zalo Channel được giữ nguyên vẹn trong hệ thống (zero code deletion).
- **SC-006**: 0 trường hợp gửi trùng lặp thông báo cho cùng một mốc đếm ngược của một nhiệm vụ.
- **SC-007**: 100% nhiệm vụ đã nộp hoặc được duyệt miễn trừ không phát sinh thêm thông báo nhắc việc ở các mốc tiếp theo.

## Assumptions

- Múi giờ chuẩn toàn hệ thống là UTC+7 (Asia/Ho_Chi_Minh).
- Chu kỳ quét định kỳ của hệ thống duy trì mỗi 30 phút một lần để bắt kịp các mốc đếm ngược trong khoảng dung sai đã định.
- Kênh Zalo Bot có thể được bật lại dễ dàng thông qua cờ cấu hình hoặc đăng ký kênh mà không cần phải viết lại code.
