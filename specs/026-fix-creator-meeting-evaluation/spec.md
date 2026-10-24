# Feature Specification: Cho phép người tạo buổi sinh hoạt không phải Admin thực hiện đánh giá buổi học và học viên

**Feature Branch**: `026-fix-creator-meeting-evaluation`

**Created**: 2026-10-24

**Status**: Draft

**Input**: User description: "Hiện tại bị lỗi người tạo meeting không phải admin không đánh giá được buổi sinh hoạt, không nút đánh giá trên UI luôn"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Người tạo buổi sinh hoạt đánh giá tổng thể buổi học và từng học viên (Priority: P1)

Là một thành viên (Trainer / Người tổ chức buổi sinh hoạt) không có quyền Quản trị viên (Admin), tôi muốn có thể nhìn thấy nút đánh giá trên giao diện và thực hiện đánh giá tổng thể buổi học cũng như chấm điểm từng thành viên tham gia, để hoàn thành trách nhiệm đào tạo và tổng kết chất lượng buổi sinh hoạt.

**Why this priority**: Đây là luồng nghiệp vụ cốt lõi đang bị gián đoạn; người trực tiếp đứng lớp hoặc tạo buổi sinh hoạt không thể đánh giá buổi học nếu họ không phải là Admin cấp cao.

**Independent Test**:
- Đăng nhập bằng tài khoản không có quyền Admin nhưng là người tạo cuộc họp (hoặc Trainer được chỉ định).
- Truy cập vào trang chi tiết buổi sinh hoạt đã kết thúc (và đã bật đánh giá 2 chiều).
- Kiểm tra nút "Trainer đánh giá buổi học" xuất hiện trên phần đầu trang (Header) và các nút "Đánh giá" xuất hiện ở từng dòng học viên trong danh sách tham gia.
- Thực hiện gửi đánh giá tổng thể và gửi đánh giá cho từng học viên thành công mà không gặp lỗi phân quyền.

**Acceptance Scenarios**:

1. **Given** một buổi sinh hoạt có tính năng đánh giá được bật và đã kết thúc, **When** người tạo buổi học (không có vai trò Admin) truy cập trang chi tiết buổi học, **Then** hệ thống nhận diện đúng vai trò Trainer/Người tạo và hiển thị nút "Trainer đánh giá buổi học" trên thanh công cụ/header cùng các nút "Đánh giá" ở từng học viên trong danh sách.
2. **Given** người tạo buổi sinh hoạt mở biểu mẫu đánh giá tổng thể buổi học, **When** điền đầy đủ điểm các tiêu chí và nhận xét rồi nhấn gửi, **Then** hệ thống ghi nhận thành công đánh giá tổng thể và cập nhật trạng thái nút thành "✓ Đã đánh giá buổi học".
3. **Given** người tạo buổi sinh hoạt nhấn "Đánh giá" một học viên trong danh sách tham gia, **When** chấm điểm các tiêu chí và gửi đánh giá, **Then** hệ thống lưu trữ đánh giá thành công và cập nhật điểm số trực tiếp trên danh sách.

---

### User Story 2 - Người tạo buổi sinh hoạt kích hoạt nhanh tính năng Đánh giá 2 chiều (Priority: P2)

Là người tạo buổi sinh hoạt (không có quyền Admin), tôi muốn có thể bật tính năng "Đánh giá 2 chiều" cho buổi học nếu lúc tạo buổi chưa kịp bật, để kịp thời thu thập phản hồi từ các thành viên.

**Why this priority**: Cho phép người đứng lớp chủ động quản lý việc bật/tắt cổng đánh giá mà không cần phụ thuộc vào sự can thiệp của Quản trị viên.

**Independent Test**:
- Đăng nhập bằng tài khoản người tạo buổi học (không phải Admin).
- Truy cập buổi học đang có trạng thái "Đánh giá: Tắt".
- Kiểm tra nút "Bật Đánh giá 2 chiều" có hiển thị và có thể bấm để kích hoạt thành công.

**Acceptance Scenarios**:

1. **Given** một buổi sinh hoạt chưa bật tính năng đánh giá, **When** người tạo buổi học truy cập trang chi tiết, **Then** nút "Bật Đánh giá 2 chiều" hiển thị rõ ràng trên giao diện.
2. **Given** người tạo buổi học nhấn nút "Bật Đánh giá 2 chiều", **When** xác nhận thao tác, **Then** hệ thống kích hoạt thành công tính năng đánh giá và hiển thị nhãn "Đánh giá 2 chiều (Hạn 24h)".

---

### User Story 3 - Quản trị viên và các thành viên khác vẫn duy trì quyền hạn chuẩn (Priority: P3)

Là hệ thống quản trị, việc mở rộng quyền cho người tạo buổi học không được làm phá vỡ hoặc xung đột với quyền hạn của Quản trị viên (Admin) và quyền đánh giá ngược lại từ phía học viên (Trainee đánh giá Trainer).

**Why this priority**: Đảm bảo an toàn phân quyền, không làm hồi quy (regression) các tính năng đánh giá và quản trị đang hoạt động ổn định.

**Independent Test**:
- Kiểm tra Quản trị viên vẫn có đầy đủ quyền xem và đánh giá bất kỳ buổi sinh hoạt nào.
- Kiểm tra một học viên bình thường (không phải Admin và không phải người tạo buổi học) chỉ thấy nút "Đánh giá Trainer" và xem "Điểm của tôi", không xuất hiện các nút đánh giá tổng thể hoặc đánh giá học viên khác.

**Acceptance Scenarios**:

1. **Given** người dùng là Quản trị viên, **When** truy cập bất kỳ buổi sinh hoạt nào, **Then** luôn nhìn thấy và thực hiện được các chức năng đánh giá và quản lý buổi học.
2. **Given** người dùng là học viên tham gia bình thường (không tạo buổi học), **When** truy cập trang chi tiết buổi sinh hoạt, **Then** chỉ nhìn thấy các nút đánh giá dành cho học viên và không nhìn thấy các nút chấm điểm của Trainer.

---

### Edge Cases

- **Buổi học có người tạo bị vô hiệu hóa hoặc không xác định**: Hệ thống giữ fallback hiển thị an toàn, gán Trainer mặc định và cho phép Admin can thiệp xử lý.
- **Người tạo buổi học tự có tên trong danh sách học viên**: Hệ thống không cho phép Trainer tự chấm điểm đánh giá cho chính mình trong danh sách học viên.
- **Buổi học chưa kết thúc hoặc chưa bắt đầu**: Nút đánh giá tổng thể tuân thủ quy tắc thời gian diễn ra của buổi học, hiển thị thông báo trạng thái phù hợp nếu cổng đánh giá chưa tới giờ mở hoặc đã quá hạn 24 giờ.
- **Học viên vắng mặt (có phép hoặc không phép)**: Nút đánh giá đối với học viên đó bị vô hiệu hóa kèm chú thích rõ ràng lý do không thể đánh giá.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI lưu trữ chính xác danh tính người tạo (Creator ID) ngay khi buổi sinh hoạt được khởi tạo vào hệ thống.
- **FR-002**: Thông tin phản hồi về chi tiết buổi sinh hoạt PHẢI luôn bao gồm định danh người tạo buổi học để giao diện người dùng nhận biết chính xác chủ sở hữu.
- **FR-003**: Giao diện người dùng (cả Web và Zalo Mini App) PHẢI công nhận người tạo buổi sinh hoạt có đầy đủ quyền Trainer đối với buổi sinh hoạt đó, ngay cả khi người dùng không sở hữu vai trò Quản trị viên.
- **FR-004**: Hệ thống PHẢI hiển thị nút thao tác đánh giá tổng thể buổi sinh hoạt cho người tạo buổi học và cho Quản trị viên khi buổi học đã kết thúc và tính năng đánh giá đang bật.
- **FR-005**: Hệ thống PHẢI hiển thị nút thao tác chấm điểm từng học viên cho người tạo buổi học và cho Quản trị viên trong bảng danh sách thành viên tham dự.
- **FR-006**: Hệ thống PHẢI hiển thị nút bật nhanh tính năng đánh giá 2 chiều cho người tạo buổi học nếu tính năng này chưa được kích hoạt.
- **FR-007**: Cổng xử lý yêu cầu đánh giá (API / Backend) PHẢI cho phép người tạo buổi sinh hoạt hoặc Trainer được phân công gửi đánh giá tổng thể và gửi đánh giá học viên mà không yêu cầu bắt buộc quyền Quản trị viên toàn hệ thống.
- **FR-008**: Hệ thống PHẢI ngăn chặn người dùng không phải người tạo buổi học, không phải Trainer được phân công, và không phải Quản trị viên thực hiện hành vi đánh giá học viên hoặc đánh giá tổng thể buổi học.

### Key Entities *(include if feature involves data)*

- **Buổi sinh hoạt (Meeting)**: Thực thể đại diện cho buổi học, chứa thông tin thời gian, người tạo (Creator), Trainer được phân công, trạng thái kích hoạt đánh giá và hạn chót đánh giá.
- **Phiếu đánh giá tổng thể (Meeting Overall Evaluation)**: Thực thể liên kết 1-1 với buổi sinh hoạt, chứa điểm trung bình và các điểm tiêu chí do Trainer hoặc người tạo buổi học đánh giá cho toàn bộ buổi.
- **Phiếu đánh giá thành viên (Meeting Participant Evaluation)**: Phiếu đánh giá cá nhân 2 chiều giữa Trainer và từng học viên tham dự buổi học.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% người dùng tạo buổi sinh hoạt nhìn thấy đầy đủ các nút đánh giá phù hợp trên giao diện Web và ứng dụng di động ngay sau khi buổi sinh hoạt kết thúc.
- **SC-002**: Tỷ lệ gửi đánh giá thành công của người tạo buổi học (không có quyền Admin) đạt 100% mà không gặp lỗi từ chối quyền truy cập (403 Forbidden).
- **SC-003**: Thời gian hoàn thành thao tác mở biểu mẫu đánh giá của người tạo buổi sinh hoạt dưới 2 giây kể từ khi truy cập chi tiết buổi học.
- **SC-004**: Không có bất kỳ sự suy giảm hay gián đoạn nào đối với quyền đánh giá của Quản trị viên và quyền đánh giá Trainer của học viên thông thường (Zero Regression).

## Assumptions

- Người dùng tạo buổi học đã được xác thực danh tính hợp lệ trên hệ thống.
- Người tạo buổi học đóng vai trò là Trainer hoặc Người phụ trách chính của buổi sinh hoạt đó, do đó được trao toàn quyền chuyên môn đánh giá học viên và buổi học.
- Quy định thời hạn đánh giá 2 chiều trong vòng 24 giờ sau khi kết thúc buổi sinh hoạt vẫn được áp dụng bình đẳng cho mọi vai trò đánh giá.
- Quyền đánh giá buổi sinh hoạt được phân cấp theo phạm vi từng buổi học (Resource-based Access Control), không đòi hỏi cấp quyền quản trị trên toàn bộ hệ thống.
