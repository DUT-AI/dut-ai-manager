# Feature Specification: Automated Task & Deadline Reminder System (Multi-Channel: Discord DM & Web In-App Management Page)

**Feature Branch**: `019-task-deadline-reminder`

**Created**: 2026-10-21 (Cập nhật: Trang Quản lý Thông báo riêng biệt trên Sidebar Menu)

**Status**: Ready for Planning

**Input**: User description: "Tôi muốn làm hệ thống tự động nhắc nhở những công việc, task phải làm của thành viên trước khi đến hạn để đỡ bị hệ thống tạo vi phạm tự động. Giao diện xem thông báo phải là 1 tab/trang quản lý như các tab quản lý khác trên web."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Thành viên nhận tin nhắn nhắc nhở trực tiếp (Direct Message) qua Discord Bot trước hạn (Priority: P1)

Là một thành viên trong nhóm, tôi muốn nhận được tin nhắn trực tiếp (DM) riêng tư từ Discord Bot nhắc nhở chi tiết các công việc (Bài tập - Homework, Trực nhật - Duty, Đánh giá cuộc họp - Meeting Evaluation) mà tôi chưa hoàn thành trước khi đến hạn chót, để tôi kịp nộp bài hoặc thực hiện nghĩa vụ, tránh bị hệ thống quét tự động phạt vi phạm (violation) vào cuối ngày.

**Why this priority**: Kênh Discord DM đảm bảo gửi thông báo tức thì đến thiết bị cá nhân của thành viên dù họ không mở trình duyệt web.

**Independent Test**:
- Tạo một bài tập hoặc lịch trực có hạn chót sắp đến với trạng thái thành viên chưa nộp (có liên kết tài khoản `discord_id`).
- Chạy quy trình kiểm tra nhắc nhở (Reminder Job).
- Xác minh rằng Discord Bot mở kênh DM trực tiếp với thành viên đó và gửi embed nhắc nhở chi tiết (tên công việc, loại task, thời hạn chót theo giờ UTC+7, thời gian đếm ngược còn lại).

**Acceptance Scenarios**:
1. **Given** một thành viên chưa hoàn thành bài tập (Homework) có deadline sắp tới, **When** hệ thống kích hoạt quét nhắc nhở theo khung giờ hoặc mốc thời gian trước hạn, **Then** Discord Bot gửi tin nhắn DM trực tiếp đến tài khoản Discord của thành viên nêu rõ tên bài tập, deadline và cảnh báo vi phạm.
2. **Given** một thành viên được phân công lịch trực vệ sinh (Cleaning Duty) của ngày hôm nay chưa nộp minh chứng, **When** đến các khung giờ nhắc nhở trong ngày (ví dụ 19:30 hoặc 22:00), **Then** thành viên nhận được tin nhắn DM từ Bot nhắc nộp ảnh minh chứng trước giờ đóng cổng điểm danh/phạt.
3. **Given** thành viên đã nộp bài tập hoặc đã hoàn thành nhiệm vụ trước thời điểm quét, **When** tiến trình quét nhắc nhở chạy, **Then** thành viên đó được bỏ qua và không nhận tin nhắn nhắc nhở.

---

### User Story 2 - Trang Quản lý Thông báo trên Sidebar Menu (`/dashboard/notifications`) (Priority: P1) 🎯 Core Web UI

Là một thành viên hoặc quản trị viên trong hệ thống, tôi muốn có một Tab riêng mang tên **"Thông báo của tôi" / "Quản lý Thông báo"** (`/dashboard/notifications`) nằm trên thanh Menu bên trái (Sidebar) cùng với icon chuông (`BellOutlined`) kèm badge đếm số lượng chưa đọc. Khi truy cập vào trang này:
- Tôi có thể xem danh sách toàn bộ các thông báo nhắc việc & hệ thống dưới dạng bảng dữ liệu hoặc thẻ trực quan chuẩn mực (Bộ lọc theo loại task: Bài tập, Trực nhật, Cuộc họp, Trạng thái: Chưa đọc / Đã đọc).
- Có thanh hành động: "Đánh dấu tất cả đã đọc", "Làm mới danh sách".
- Bấm vào một thông báo để xem chi tiết và nhấp liên kết chuyển thẳng đến trang nộp bài tập hoặc ca trực nhật.
- Phân trang đầy đủ (`defaultPageSize >= 20`) theo đúng chuẩn Hiến pháp Principle VIII.

**Why this priority**: Đáp ứng trực tiếp và chính xác yêu cầu của người dùng: giao diện xem thông báo là một tab trang chuyên nghiệp, đồng bộ với các màn hình quản lý hiện có (như Quản lý Bài tập, Quản lý Trực nhật, Quản lý Vi phạm), mang lại trải nghiệm tra cứu và xử lý công việc tập trung. Không cần tính năng xóa thông báo để đảm bảo tính toàn vẹn lịch sử và đơn giản hóa trải nghiệm (tập trung vào Đã đọc / Chưa đọc).

**Independent Test**:
- Đăng nhập vào web, bấm vào menu **"Thông báo"** trên Sidebar (`/dashboard/notifications`).
- Kiểm tra danh sách hiển thị các thông báo nhắc việc bài tập/trực nhật với đầy đủ badge trạng thái (Chưa đọc/Đã đọc), mức độ khẩn cấp (Warning, Urgent), bộ lọc danh mục và phân trang.
- Bấm "Đánh dấu đã đọc" một hoặc toàn bộ thông báo $\rightarrow$ Trạng thái chuyển đổi ngay lập tức và badge menu giảm tương ứng.

**Acceptance Scenarios**:
1. **Given** người dùng truy cập web, **When** nhìn vào thanh Sidebar Menu, **Then** thấy mục "Thông báo" kèm badge đếm số lượng thông báo chưa đọc.
2. **Given** người dùng nhấp vào mục "Thông báo", **When** trang `/dashboard/notifications` tải, **Then** hiển thị đầy đủ bảng danh sách thông báo, bộ lọc (Tất cả, Bài tập, Trực nhật, Meeting) và phân trang chuẩn.
3. **Given** người dùng bấm nút "Nộp bài ngay" trên một dòng thông báo, **When** hệ thống xử lý, **Then** đánh dấu thông báo là đã đọc và chuyển hướng người dùng đến trang nộp bài tương ứng.
4. **Given** người dùng bấm "Đánh dấu tất cả đã đọc", **When** xác nhận, **Then** toàn bộ thông báo của người dùng chuyển thành đã đọc và badge trên Sidebar Menu biến mất.

---

### User Story 3 - Lập lịch quét nhắc nhở Hybrid kết hợp & Đa kênh (Discord DM + Web In-App) (Priority: P2)

Là một Quản trị viên hệ thống (Admin / Team Leader), tôi muốn hệ thống tự động quét theo chiến lược Hybrid:
1. **4 Khung giờ cố định hàng ngày**: `08:00`, `12:00`, `19:30`, `22:00` (giờ UTC+7).
2. **5 Mốc đếm ngược động theo deadline**: Trước `2 ngày`, trước `1 ngày`, trước `12 giờ`, trước `4 giờ`, và trước `1 giờ`.
Mỗi khi phát hiện task chưa làm, hệ thống đồng thời:
- Gửi tin nhắn DM Discord tới thành viên.
- Tạo bản ghi trong cơ sở dữ liệu `notifications` để hiển thị trên web, đồng thời lưu vết chống gửi lặp (idempotency) và quản lý cooldown 3h.

**Why this priority**: Tự động hóa 24/7, gắn kết thông báo giữa Discord và Web, phòng ngừa vi phạm triệt để.

---

### User Story 4 - Ban quản trị theo dõi nhật ký nhắc việc và kiểm tra chạy thủ công (Priority: P3)

Là một Quản trị viên, tôi muốn có nút "Kích hoạt quét nhắc nhở ngay" (Manual Run) trên trang Quản lý hoặc qua API để kiểm thử tính năng phát thông báo mà không cần đợi lịch cronjob.

---

### Edge Cases

- **Chống spam trùng lặp (Deduplication)**: Cùng một task và cùng một mốc nhắc nhở chỉ tạo đúng 1 bản ghi `Notification` và gửi 1 tin nhắn Discord DM.
- **Thành viên khóa DM Discord**: Không làm ảnh hưởng đến việc tạo thông báo trên trang web của thành viên đó (Fault Isolation). Trạng thái gửi Discord được lưu vết trong thuộc tính `discord_status` của bản ghi Notification.
- **Thành viên đã nộp bài/đã xin phép**: Tự động loại trừ, không tạo thông báo rác và không gửi tin DM.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI có khả năng tự động quét các nhiệm vụ có hạn chót và xác định danh sách thành viên chưa hoàn thành (Bài tập, Lịch trực nhật, Đánh giá cuộc họp).
- **FR-002**: Hệ thống PHẢI hỗ trợ cơ chế quét lịch nhắc nhở Hybrid kết hợp (4 khung giờ cố định: `08:00`, `12:00`, `19:30`, `22:00` và 5 mốc đếm ngược: `2 ngày`, `1 ngày`, `12h`, `4h`, `1h`).
- **FR-003**: Hệ thống PHẢI hỗ trợ phân phối thông báo đa kênh đồng bộ:
  - **Discord**: Tin nhắn trực tiếp (Direct Message - DM) gửi từ Bot kèm Discord Embed chi tiết.
  - **Web In-App**: Lưu trữ thông báo trong bảng `notifications` hiển thị trên Tab Quản lý Thông báo.
- **FR-004**: Frontend PHẢI thêm một tab/trang quản lý riêng biệt tại đường dẫn `/dashboard/notifications`, xuất hiện trên thanh Sidebar Menu (`frontend/src/config/menu.tsx`) với icon `BellOutlined` kèm badge đếm số lượng chưa đọc.
- **FR-005**: Màn hình `NotificationManagementPage` PHẢI tuân thủ Hiến pháp Principle VIII:
  - Trang chính chỉ đóng vai trò Orchestrator.
  - Các subcomponent tách biệt trong `components/`: `NotificationFilter.tsx`, `NotificationTable.tsx`, `NotificationDetailModal.tsx`.
  - Bảng dữ liệu có phân trang chuẩn (`defaultPageSize >= 20`, `pageSizeOptions: ['10', '20', '50', '100']`).
  - Không có tính năng xóa thông báo để bảo toàn nhật ký thông báo tập trung.
- **FR-006**: Backend PHẢI cung cấp đầy đủ các REST API cho Notifications:
  - `GET /api/v1/notifications/my`: Lấy danh sách thông báo phân trang có bộ lọc (`category`, `is_read`, `page`, `page_size`).
  - `GET /api/v1/notifications/unread-count`: Đếm số lượng thông báo chưa đọc.
  - `PATCH /api/v1/notifications/{id}/read`: Đánh dấu 1 thông báo đã đọc.
  - `POST /api/v1/notifications/read-all`: Đánh dấu tất cả đã đọc.
- **FR-007**: Hệ thống PHẢI sử dụng một bảng `notifications` duy nhất để vừa hiển thị thông báo cho người dùng trên Web, vừa lưu trữ metadata kỹ thuật (`task_type`, `task_id`, `reminder_stage`, `discord_status`, `error_message`) để đảm bảo tính Idempotent (chống trùng) và kiểm soát cooldown 3 giờ giữa các lần nhắc nhở.
- **FR-008**: Quản trị viên PHẢI có endpoint để kích hoạt quét nhắc nhở thủ công (`POST /api/v1/reminders/trigger`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Giảm ít nhất 40% tỷ lệ vi phạm phát sinh tự động do trễ hạn bài tập và nhiệm vụ trực nhật sau 1 tháng triển khai.
- **SC-002**: 100% thành viên có thể mở tab "Thông báo" trên Sidebar Menu để kiểm tra toàn bộ nhiệm vụ và nhắc nhở của mình.
- **SC-003**: Thời gian phản hồi API lấy danh sách thông báo và số lượng chưa đọc dưới 100ms.
- **SC-004**: 0 trường hợp gửi lặp thông báo cho cùng một mốc thời gian nhắc nhở.
- **SC-005**: Thao tác đánh dấu đã đọc hoặc chuyển đến bài tập từ trang Thông báo phản hồi tức thì dưới 1 giây.

## Assumptions

- Múi giờ chuẩn toàn hệ thống là UTC+7 (Asia/Ho_Chi_Minh).
- Menu bên trái hiển thị cho tất cả thành viên đã đăng nhập hệ thống.
