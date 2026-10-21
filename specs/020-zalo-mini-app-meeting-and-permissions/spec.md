# Feature Specification: Đồng Bộ Tính Năng Lịch Meeting & Quản Lý Đơn Phép Trên Zalo Mini App

**Feature Branch**: `020-zalo-mini-app-meeting-and-permissions`

**Created**: 2026-10-21

**Status**: Draft

**Input**: User description: "Ở phần zalo mini app ở thư mục zalo mini app tôi muốn có các giao diện quản lý đơn phép và các chức năng của lịch meeting như ở WEB"

## Clarifications

### Session 2026-10-21
- Q: Khi bấm vào một buổi họp trên Zalo Mini App, hiển thị màn hình Chi tiết Buổi họp (Meeting Detail) theo dạng nào? → A: Sử dụng trang riêng biệt (`MeetingDetailPage`) với route riêng (`/meetings/:id`) để có không gian rộng rãi cho các tab Người tham gia và Đánh giá tương tự Web.
- Q: Về phần Đánh giá buổi họp (Evaluation) của Host/Trainer trên Zalo Mini App, tích hợp theo hướng nào? → A: Tích hợp trực tiếp các tab: "Người tham gia", "Đánh giá Trainee", và "Tổng kết đánh giá" ngay trên `MeetingDetailPage` như Web.
- Q: Đối với giao diện Quản lý Đơn xin phép, phân quyền và chế độ hiển thị danh sách hoạt động như thế nào? → A: Hiển thị như bản Web: mặc định hiển thị tất cả các đơn mà người dùng có quyền xem/quản lý, kèm đầy đủ các bộ lọc (lọc theo danh mục đơn, trạng thái, người tạo/đơn của tôi).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Thành viên xem và thao tác đầy đủ thông tin buổi họp trên Zalo Mini App (Priority: P1)

Thành viên hoặc ban cán sự mở Zalo Mini App để theo dõi lịch sinh hoạt / meeting. Người dùng có thể xem danh sách meeting theo tuần/tháng, xem chi tiết buổi họp với đầy đủ thông số như trên WEB: Hero header tóm tắt (thời gian, địa điểm, phòng, số ghế tối đa, trạng thái), thống kê sĩ số tham gia (số người tham gia, vắng có phép, vắng không phép, đi trễ), danh sách người tham dự kèm trạng thái chi tiết, và thực hiện điểm danh (Check-in ảnh/mã).

**Why this priority**: Lịch meeting là tính năng cốt lõi được sử dụng thường xuyên nhất bởi thành viên khi di động, giúp họ nắm rõ lịch, phòng họp và sĩ số mà không cần mở máy tính.

**Independent Test**:
- Đăng nhập tài khoản thành viên trên Zalo Mini App.
- Vào trang Lịch Meeting -> Chọn một buổi họp cụ thể.
- Kiểm tra hiển thị đầy đủ: thông tin chung (thời gian, địa điểm, link họp), thẻ thống kê số lượng tham gia/vắng/trễ, danh sách người tham gia với tag trạng thái.
- Thành viên bấm điểm danh -> gửi ảnh hoặc xác nhận thành công.

**Acceptance Scenarios**:
1. **Given** Buổi họp có 20 thành viên tham gia (trong đó có 2 người xin vắng, 1 người đi trễ), **When** Người dùng mở chi tiết buổi họp trên Zalo Mini App, **Then** Giao diện hiển thị đúng thẻ thống kê (Tổng tham gia: 20, Vắng: 2, Trễ: 1) và danh sách người tham gia phân loại rõ ràng.
2. **Given** Người dùng là người tham gia buổi họp đang diễn ra và chưa điểm danh, **When** Người dùng bấm nút điểm danh tải ảnh chụp tại phòng họp, **Then** Trạng thái của người dùng cập nhật thành "Đã tham gia" / "Có mặt" và số liệu sĩ số tự động tăng.

---

### User Story 2 - Quản trị viên / Host quản lý người tham dự & đánh giá buổi họp trên Zalo Mini App (Priority: P2)

Người chủ trì (Host) hoặc Quản trị viên có quyền cập nhật nhanh trạng thái của từng người tham gia (Đã tham gia, Vắng, Trễ, Hủy), duyệt/check-in hàng loạt, và thực hiện đánh giá buổi họp (Trainee Evaluation, Trainer Evaluation, Overall Evaluation) tương tự như trên hệ thống WEB.

**Why this priority**: Người điều hành thường xuyên sử dụng điện thoại khi đang trực tiếp tại phòng họp sinh hoạt để điểm danh và đánh giá thành viên trực tiếp theo thời gian thực.

**Independent Test**:
- Đăng nhập với quyền Host/Admin trên Zalo Mini App.
- Mở danh sách người tham dự trong buổi họp.
- Chọn một thành viên và đổi trạng thái (ví dụ từ Chờ sang Có mặt).
- Mở modal đánh giá thành viên (Trainee Evaluation), nhập điểm/nhận xét và lưu thành công.

**Acceptance Scenarios**:
1. **Given** Host đang chủ trì buổi họp có bật tính năng đánh giá (`enable_evaluation = true`), **When** Host chọn thành viên trong tab Đánh giá và chấm điểm tiêu chí, **Then** Đánh giá được lưu lại thành công và hiển thị tiến độ đánh giá của buổi họp.
2. **Given** Host muốn điều chỉnh thủ công trạng thái của một người vắng mặt, **When** Host chọn "Chỉnh sửa trạng thái" và lưu, **Then** Trạng thái người tham gia cập nhật ngay lập tức.

---

### User Story 3 - Quản lý đơn phép đầy đủ các loại (Đổi buổi sinh hoạt, Đi trễ, Vắng, Hoãn bài tập) trên Zalo Mini App (Priority: P3)

Thành viên gửi các loại đơn xin phép linh hoạt ngay trên Zalo Mini App:
1. Đơn xin đổi buổi sinh hoạt (`CHANGE_MEETING`): Chọn buổi họp hiện tại (hoặc Đăng ký mới) và chọn buổi họp đích trong tương lai, tự động kiểm tra số ghế còn trống và duyệt tự động nếu còn chỗ.
2. Đơn xin vắng sinh hoạt (`ABSENCE`), Đi trễ (`LATE`) kèm chọn giờ có mặt, Hoãn bài tập (`POSTPONE`) kèm chọn hạn nộp mới và liên kết bài tập.
Người dùng có thể xem lịch sử đơn của mình, xem chi tiết lý do/phê duyệt, chỉnh sửa hoặc hủy đơn khi chưa quá hạn. Quản trị viên có thể xem toàn bộ đơn của nhóm/tất cả thành viên và lọc theo trạng thái/loại đơn.

**Why this priority**: Giúp giải quyết nhu cầu phát sinh khi bận đột xuất ngay trên thiết bị di động, đồng bộ 100% nghiệp vụ đơn phép giữa Web và Zalo.

**Independent Test**:
- Thành viên mở trang Quản lý đơn phép trên Zalo Mini App.
- Tạo đơn "Đổi buổi sinh hoạt": chọn buổi họp đích B còn 3 chỗ.
- Gửi đơn -> Đơn được tạo và duyệt tự động (chuyển ca thành công), danh sách buổi họp cập nhật tương ứng.
- Lọc danh sách đơn theo từng loại (`CHANGE_MEETING`, `ABSENCE`, `LATE`, `POSTPONE`).

**Acceptance Scenarios**:
1. **Given** Thành viên chọn loại đơn "Đổi buổi sinh hoạt" sang Meeting B còn chỗ, **When** Thành viên bấm gửi đơn, **Then** Hệ thống ghi nhận đơn, tự động duyệt và rút thành viên khỏi buổi cũ sang buổi mới.
2. **Given** Buổi họp B đã hết chỗ (Ghế còn lại = 0), **When** Thành viên cố gắng tạo đơn chuyển sang B, **Then** Hệ thống cảnh báo buổi họp đã hết chỗ và không cho gửi.

---

### Edge Cases

- **Mất kết nối mạng khi đang thao tác:** Khi người dùng điểm danh tải ảnh hoặc gửi đơn xin phép mà mạng chập chờn, hệ thống hiển thị thông báo lỗi rõ ràng và giữ lại dữ liệu form để người dùng gửi lại.
- **Meeting diễn ra trong quá khứ:** Không cho phép tạo đơn xin vắng/đổi ca cho các buổi họp đã kết thúc nếu vi phạm quy định về thời gian nộp đơn.
- **Xung đột ghế trống đồng thời:** Hai thành viên cùng lúc đổi sang 1 ghế cuối cùng của buổi họp; hệ thống xử lý người đến trước thành công, người thứ hai nhận thông báo hết chỗ.
- **Phân quyền thao tác:** Người dùng thông thường chỉ xem và sửa/xóa đơn của chính mình; không thể truy cập các nút chỉnh sửa sĩ số hoặc đánh giá của Host nếu không có quyền `meetings:update` hoặc không phải Host.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống MUST hiển thị lịch họp (Meeting Calendar) trên Zalo Mini App với 2 chế độ hiển thị: Dạng tuần (Weekly Timeline/List) và Dạng tháng (Monthly Calendar).
- **FR-002**: Khi người dùng nhấn vào một buổi họp, hệ thống MUST điều hướng sang trang Chi tiết Buổi họp riêng biệt (`MeetingDetailPage`) bao gồm: Hero Header (tiêu đề, thời gian bắt đầu - kết thúc, phòng/địa điểm, đường dẫn tham gia, số lượng ghế tối đa), Thẻ thống kê sĩ số (Tổng tham gia, Có mặt/Đã tham gia, Vắng có phép, Vắng không phép, Đi trễ).
- **FR-003**: Hệ thống MUST hiển thị danh sách người tham gia (Participants List) phân nhóm rõ ràng theo trạng thái, hiển thị thông tin avatar, tên, vai trò và trạng thái tham gia.
- **FR-004**: Người dùng tham gia MUST có thể thực hiện Điểm danh (Check-in) thông qua chụp ảnh tải lên từ camera hoặc thư viện điện thoại khi buổi họp đang diễn ra.
- **FR-005**: Trên trang `MeetingDetailPage`, hệ thống MUST hỗ trợ các Tab chuyên biệt bao gồm: "Người tham gia", "Đánh giá Trainee", và "Tổng kết đánh giá". Người dùng có quyền (Host/Admin) MUST có thể điều chỉnh trạng thái người tham gia và thực hiện chấm điểm/đánh giá trực tiếp.
- **FR-006**: Hệ thống MUST cung cấp giao diện Quản lý Đơn xin phép hoàn chỉnh với đầy đủ 5 danh mục đơn: Vắng sinh hoạt (`ABSENCE`), Đi trễ (`LATE`), Hoãn bài tập (`POSTPONE`), Đổi buổi sinh hoạt (`CHANGE_MEETING`), và Khác (`OTHER`).
- **FR-007**: Với đơn Đổi buổi sinh hoạt (`CHANGE_MEETING`), giao diện MUST cho phép chọn ca hiện tại (hoặc chưa có lịch) và chọn ca đích, đồng thời hiển thị thông tin số ghế trống và cảnh báo khi ca đích đã hết chỗ.
- **FR-008**: Giao diện danh sách đơn phép MUST hiển thị danh sách tất cả các đơn mà tài khoản có quyền truy cập như bản Web, tích hợp thanh bộ lọc đa năng (theo loại đơn, trạng thái, và đơn của tôi).
- **FR-009**: Hệ thống MUST cho phép xem chi tiết đơn phép (kèm thông tin người nộp, thời gian, buổi họp/bài tập liên kết, lý do) và hỗ trợ chỉnh sửa / hủy đơn đối với đơn của chính người dùng khi chưa đóng.

---

## Success Criteria *(measurable, tech-agnostic)*

1. **Độ tương đồng chức năng**: Đạt 100% các luồng chức năng cốt lõi của Lịch Meeting (xem lịch, xem chi tiết, thống kê sĩ số, danh sách người tham gia, điểm danh, đổi ca) và Quản lý Đơn phép từ Web sang Zalo Mini App.
2. **Thời gian hoàn thành thao tác**: Người dùng có thể hoàn thành việc nộp một đơn xin phép (bao gồm đơn đổi ca sinh hoạt) hoặc thực hiện điểm danh buổi họp trong vòng dưới 30 giây trên thiết bị di động.
3. **Độ phản hồi và tính sẵn sàng**: Tải dữ liệu lịch meeting và danh sách đơn phép hiển thị cho người dùng trong vòng dưới 1.5 giây trong điều kiện mạng thông thường.
4. **Tỷ lệ thao tác thành công**: 95% thao tác điểm danh và nộp đơn xin phép của thành viên diễn ra suôn sẻ, không gặp lỗi giao diện hoặc mất dữ liệu form.

---

## Key Entities

- **Meeting (Buổi sinh hoạt/họp)**: Bao gồm mã định danh, tiêu đề, nội dung, thời gian bắt đầu, thời gian kết thúc, địa điểm, sức chứa tối đa (max seat), cấu hình điểm danh/đánh giá, danh sách người tham gia.
- **Participant (Người tham gia)**: Liên kết giữa người dùng và buổi họp, vai trò (Host, Trainer, Trainee), trạng thái tham dự (REGISTERED, JOINED, ABSENT, LATE, CANCELLED), ghi chú và kết quả đánh giá.
- **PermissionRequest (Đơn xin phép)**: Mã đơn, người tạo, loại đơn (`ABSENCE`, `LATE`, `POSTPONE`, `CHANGE_MEETING`, `OTHER`), buổi họp liên quan (meeting_id, old_meeting_id), bài tập liên quan, thời gian có mặt/deadline mới, lý do và trạng thái xử lý.
- **Evaluation (Đánh giá buổi họp)**: Tiêu chí chấm điểm, nhận xét của Trainer/Host dành cho Trainee hoặc đánh giá tổng quan buổi họp.
