# Feature Specification: Đánh Giá 2 Chiều Cá Nhân Buổi Học (Trainer & Trainee)

**Feature Branch**: `004-meeting-evaluation`

**Created**: 2026-10-02

**Status**: Draft

**Input**: User description: "Tôi mong muốn làm 1 tính năng tạo meeting, trong đó người tạo phải đánh giá các member trong meeting đó, và ngược lại người tham gia phải có trách nhiệm đánh giá meeting đó, các tiêu chí đánh giá thì bạn có thể tìm hiểu giúp tôi, bối cảnh, meeting là 1 lớp học, người tạo là trainer, người tham gia là trainee. Cập nhật: Đánh giá nhắm vào cá nhân (Trainee đánh giá Trainer, Trainer đánh giá Trainee), reviewer có thể ẩn danh nhưng dữ liệu ID vẫn lưu trong hệ thống để quản trị, chỉ ẩn đi khi hiển thị cho người dùng."

## Clarifications

### Session 2026-10-02
- Q: Nghĩa vụ và chế tài đánh giá của Trainee và Trainer nên được xử lý theo cơ chế nào? → A: Bắt buộc hoàn thành đánh giá trong thời hạn 24 giờ kể từ khi kết thúc buổi học. Nếu quá 24h mà Trainer hoặc Trainee chưa hoàn thành đánh giá, hệ thống sẽ tự động tạo 01 biên bản vi phạm (`Violation`) cho người đó, đồng thời tạm khóa quyền xem kết quả chi tiết.
- Q: Bộ tiêu chí đánh giá (Evaluation Criteria) nên được quản lý theo mô hình nào? → A: Sử dụng bộ tiêu chí cố định hệ thống (System Defaults) gồm 4 tiêu chí chuẩn hóa cho mỗi chiều đánh giá cá nhân (Trainer đánh giá Trainee và Trainee đánh giá Trainer).
- Q: Quyền riêng tư / Tính ẩn danh của Trainee khi đánh giá Trainer nên được thiết lập ra sao? → A: Cho phép Trainee chủ động chọn tùy chọn "Gửi ẩn danh". **Hệ thống vẫn lưu trữ chính xác ID người đánh giá trong cơ sở dữ liệu** để phục vụ quản trị, đối soát vi phạm và ngăn chặn trùng lặp, nhưng sẽ **ẩn danh tính người gửi ở tầng giao diện/API hiển thị cho Trainer**.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Trainer tạo buổi học và cấu hình cơ chế đánh giá 2 chiều cá nhân (Priority: P1)

Trainer (người tạo meeting/lớp học) tạo một buổi học mới với danh sách Trainee tham gia. Buổi học có tùy chọn bật cơ chế đánh giá bắt buộc 2 chiều (Trainer đánh giá từng Trainee và Trainee đánh giá Trainer) sau khi buổi học kết thúc với thời hạn đánh giá xác định (mặc định 24h).

**Why this priority**: Đây là điểm khởi đầu cho toàn bộ vòng đời của buổi học có đánh giá, thiết lập danh sách người tham gia cần được đánh giá và người chịu trách nhiệm đánh giá.

**Independent Test**: Trainer tạo một buổi học với danh sách 3 Trainee, bật cờ yêu cầu đánh giá 2 chiều (`enable_evaluation = true`). Kiểm tra buổi học được lưu thành công và sẵn sàng chuyển sang trạng thái chờ đánh giá khi lớp học kết thúc.

**Acceptance Scenarios**:

1. **Given** Trainer đang ở giao diện tạo Meeting/Buổi học, **When** Trainer nhập thông tin (tiêu đề, thời gian, danh sách Trainee) và kích hoạt chế độ "Đánh giá 2 chiều", **Then** hệ thống khởi tạo buổi học với cấu hình đánh giá tương ứng và hạn chót đánh giá (24h sau kết thúc).
2. **Given** buổi học đã được tạo thành công, **When** Trainee xem chi tiết lịch học, **Then** Trainee thấy thông tin lớp học cùng thông báo về nghĩa vụ đánh giá Trainer và hạn chót hoàn thành trong 24h sau buổi học.

---

### User Story 2 - Trainer đánh giá từng Trainee sau buổi học (Priority: P1)

Sau khi buổi học kết thúc (hoặc chuyển sang trạng thái hoàn thành), Trainer truy cập vào danh sách học viên của buổi học để chấm điểm và nhận xét chi tiết từng Trainee theo bộ 4 tiêu chí học tập chuẩn hóa của hệ thống.

**Why this priority**: Cốt lõi của việc quản lý chất lượng đào tạo, ghi nhận sự tiến bộ, mức độ tham gia và thái độ chuẩn bị của từng học viên trong buổi học.

**Independent Test**: Trainer mở danh sách học viên của lớp đã học xong, chọn 1 Trainee và gửi phiếu đánh giá gồm 4 tiêu chí chuẩn (Chuyên cần & Tác phong, Mức độ Tương tác & Đóng góp, Mức độ Tiếp thu & Hiểu bài, Mức độ Chuẩn bị bài trước buổi học) kèm nhận xét. Kiểm tra kết quả đánh giá được lưu chính xác và tính điểm trung bình cho Trainee.

**Acceptance Scenarios**:

1. **Given** buổi học đã hoàn thành, **When** Trainer mở trang đánh giá học viên, **Then** hệ thống hiển thị danh sách tất cả Trainee kèm trạng thái đánh giá (Chưa đánh giá / Đã đánh giá).
2. **Given** Trainer nhập điểm đánh giá theo thang điểm chuẩn (1-5 sao) cho 4 tiêu chí của một Trainee cùng nhận xét cụ thể, **When** Trainer bấm lưu đánh giá, **Then** hệ thống ghi nhận phiếu đánh giá và cập nhật trạng thái của Trainee đó thành "Đã đánh giá".
3. **Given** Trainer chưa đánh giá hết tất cả Trainee trong danh sách, **When** Trainer xem tổng quan buổi học, **Then** hệ thống hiển thị tiến độ đánh giá của Trainer (ví dụ: "Đã đánh giá 4/5 Trainee").

---

### User Story 3 - Trainee đánh giá Trainer với tùy chọn ẩn danh (Priority: P1)

Trainee sau khi tham gia lớp học có trách nhiệm gửi phản hồi/đánh giá trực tiếp cho Trainer theo bộ 4 tiêu chí giảng dạy chuẩn hóa (Chất lượng Nội dung bài học, Phương pháp Giảng dạy & Hỗ trợ, Không khí Lớp học & Sự tương tác, Giá trị Thu nhận & Tính ứng dụng) kèm góp ý cải thiện. Trainee có quyền chủ động tick chọn "Gửi ẩn danh".

**Why this priority**: Giúp nâng cao chất lượng giảng dạy thông qua phản hồi thực tế từ học viên dành cho Trainer, đảm bảo tính minh bạch và 2 chiều của môi trường giáo dục.

**Independent Test**: Trainee đăng nhập vào hệ thống, truy cập buổi học vừa tham gia, điền biểu mẫu đánh giá Trainer, chọn ẩn danh hoặc không, và gửi thành công.

**Acceptance Scenarios**:

1. **Given** Trainee đã tham gia buổi học và chưa thực hiện đánh giá Trainer, **When** Trainee truy cập trang chi tiết buổi học hoặc nhận thông báo nhắc nhở, **Then** hệ thống hiển thị biểu mẫu đánh giá Trainer với tùy chọn "Gửi ẩn danh".
2. **Given** Trainee chấm điểm 4 tiêu chí chất lượng, nhập ý kiến đóng góp và chọn "Gửi ẩn danh", **When** Trainee nhấn gửi đánh giá, **Then** hệ thống lưu đầy đủ ID người đánh giá trong DB nhưng mask/ẩn danh tính đối với Trainer khi xem kết quả.
3. **Given** Trainee đã hoàn thành gửi đánh giá Trainer, **When** Trainee xem lại chi tiết buổi học, **Then** Trainee được mở khóa xem kết quả đánh giá và lời nhận xét mà Trainer dành riêng cho mình.

---

### User Story 4 - Báo cáo tổng hợp, chế tài hạn chót 24h và tự động tạo vi phạm (Priority: P2)

Trainer, Quản lý đào tạo (Admin) và Trainee có thể xem báo cáo tổng hợp kết quả đánh giá: điểm trung bình, phân tích các tiêu chí mạnh/yếu, và danh sách các thành viên chưa hoàn thành nghĩa vụ đánh giá. Tác vụ định kỳ tự động quét và tạo biên bản vi phạm cho Trainer/Trainee chưa hoàn thành đánh giá sau 24h.

**Why this priority**: Cung cấp bức tranh toàn diện về chất lượng buổi học và đảm bảo kỷ luật đánh giá bắt buộc 2 chiều bằng cơ chế vi phạm tự động.

**Independent Test**: Giả lập buổi học đã kết thúc quá 24h, kích hoạt tác vụ kiểm tra đánh giá và xác minh các trường hợp Trainer chưa đánh giá Trainee hoặc Trainee chưa đánh giá Trainer bị tự động tạo biên bản `Violation`.

**Acceptance Scenarios**:

1. **Given** Trainer xem phản hồi đánh giá từ các Trainee, **When** Trainer mở báo cáo, **Then** các đánh giá có `is_anonymous = true` hiển thị người gửi là "Học viên ẩn danh" mà không lộ thông tin cá nhân.
2. **Given** sau 24 giờ kể từ khi buổi học kết thúc mà Trainee chưa hoàn thành đánh giá Trainer, **When** tác vụ quét chạy, **Then** hệ thống tự động tạo 01 biên bản vi phạm ("Chưa hoàn thành đánh giá Trainer trong 24h") cho Trainee đó và khóa quyền xem điểm đánh giá từ Trainer.
3. **Given** sau 24 giờ kể từ khi buổi học kết thúc mà Trainer chưa hoàn tất đánh giá cho các Trainee, **When** tác vụ quét chạy, **Then** hệ thống tự động tạo 01 biên bản vi phạm ("Trainer chưa hoàn tất đánh giá học viên trong 24h") cho Trainer.
4. **Given** Trainee đã gửi đánh giá Trainer đúng hạn trong 24h, **When** Trainee vào trang kết quả buổi học, **Then** Trainee xem được điểm số và lời nhận xét chi tiết mà Trainer dành riêng cho mình.

---

### Edge Cases

- **Trainee vắng mặt trong buổi học**: Đối với Trainee có trạng thái vắng mặt (`ABSENT_EXCUSED` hoặc `ABSENT_UNEXCUSED`), Trainer ghi nhận lý do vắng hoặc bỏ qua đánh giá; Trainee vắng mặt không có quyền đánh giá Trainer và không bị phạt vi phạm đánh giá.
- **Đánh giá trùng lặp**: Ràng buộc duy nhất `UNIQUE(meeting_id, reviewer_id, target_user_id)` đảm bảo mỗi cá nhân chỉ gửi 1 phiếu đánh giá duy nhất cho đối tượng tương ứng trong cùng một buổi học.
- **Buổi học bị hủy**: Khi buổi học bị hủy, toàn bộ quy trình và nghĩa vụ đánh giá cho buổi học đó tự động vô hiệu hóa.
- **Hết hạn đánh giá (Sau 24h)**: Trainer hoặc Trainee sau 24h chưa hoàn thành đánh giá thì hệ thống tự động tạo 01 biên bản vi phạm (`Violation`).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI cho phép Trainer bật/tắt tính năng "Đánh giá 2 chiều" (`enable_evaluation`) khi tạo hoặc cập nhật Buổi học.
- **FR-002**: Hệ thống PHẢI sử dụng bộ 4 tiêu chí cố định hệ thống (System Defaults) để Trainer đánh giá Trainee gồm:
  - *Chuyên cần & Tác phong* (Đúng giờ, tuân thủ nội quy).
  - *Mức độ Tương tác & Đóng góp* (Phát biểu, đặt câu hỏi, thảo luận nhóm).
  - *Mức độ Tiếp thu & Hiểu bài* (Nắm bắt kiến thức truyền tải).
  - *Mức độ Chuẩn bị bài trước buổi học* (Đọc trước tài liệu, chuẩn bị bài tập/môi trường trước khi lên lớp).
- **FR-003**: Hệ thống PHẢI sử dụng bộ 4 tiêu chí cố định hệ thống (System Defaults) để Trainee đánh giá Trainer gồm:
  - *Chất lượng Nội dung bài học* (Rõ ràng, thực tế, đúng tiến độ).
  - *Phương pháp Giảng dạy & Hỗ trợ của Trainer* (Nhiệt tình, giải đáp thỏa đáng, dễ hiểu).
  - *Không khí Lớp học & Sự tương tác* (Tạo động lực, lôi cuốn).
  - *Giá trị Thu nhận & Tính ứng dụng* (Mức độ tiếp thu kiến thức mới hữu ích).
- **FR-004**: Hệ thống PHẢI hỗ trợ thang điểm đánh giá chuẩn hóa từ 1 đến 5 sao cho từng tiêu chí.
- **FR-005**: Mỗi phiếu đánh giá PHẢI bao gồm cả điểm số theo 4 tiêu chí và phần nhận xét/góp ý dạng văn bản tự do (`feedback_text`).
- **FR-006**: Hệ thống PHẢI cho phép Trainer đánh giá độc lập từng Trainee tham gia buổi học và hiển thị tiến độ hoàn thành (số lượng Trainee đã/chưa được đánh giá).
- **FR-007**: Hệ thống PHẢI cho phép Trainee gửi đánh giá cá nhân cho Trainer sau khi thời gian buổi học kết thúc và bản thân có tham gia (`JOINED` hoặc `COMPLETED`).
- **FR-008**: Hệ thống PHẢI cung cấp tùy chọn "Gửi ẩn danh" (`is_anonymous`) trên biểu mẫu đánh giá của Trainee. Hệ thống PHẢI lưu chính xác ID người đánh giá trong cơ sở dữ liệu nhưng PHẢI che giấu thông tin danh tính khi hiển thị cho Trainer.
- **FR-009**: Hệ thống PHẢI áp dụng thời hạn đánh giá bắt buộc là **24 giờ** sau khi buổi học kết thúc.
- **FR-010**: Tác vụ tự động PHẢI quét các buổi học sau 24 giờ kết thúc và tự động tạo biên bản vi phạm (`Violation`) cho Trainer chưa đánh giá xong học viên hoặc Trainee có tham gia nhưng chưa đánh giá Trainer.
- **FR-011**: Hệ thống PHẢI ngăn chặn việc gửi đánh giá trùng lặp (`UNIQUE(meeting_id, reviewer_id, target_user_id)`).
- **FR-012**: Hệ thống PHẢI tính toán điểm đánh giá trung bình tổng thể và điểm trung bình theo từng tiêu chí cho Trainer và từng Trainee.
- **FR-013**: Hệ thống PHẢI tự động gửi thông báo nhắc nhở (qua Discord, Zalo hoặc Notification) cho Trainer và Trainee khi có buổi học cần hoàn thành đánh giá hoặc khi sắp hết hạn 24h.

---

### Key Entities *(include if feature involves data)*

- **Buổi học (`Meeting`)**: Được mở rộng thêm các thuộc tính: cờ kích hoạt đánh giá (`enable_evaluation`), hạn chót đánh giá (`evaluation_deadline`).
- **Đánh giá Buổi học / Cá nhân (`MeetingEvaluation`)**: Đại diện cho phiếu đánh giá giữa 2 cá nhân trong buổi học. Thuộc tính: `meeting_id`, `reviewer_id` (luôn lưu ID thực tế), `target_user_id` (luôn trỏ vào cá nhân Trainer/Trainee), `evaluation_type` (`TRAINER_TO_TRAINEE` hoặc `TRAINEE_TO_TRAINER`), `is_anonymous` (boolean), `scores` (JSONB), `average_score` (float), `feedback_text` (text), `created_at`.
- **Biên bản Vi phạm (`Violation`)**: Thực thể thuộc domain Vi phạm, được tự động tạo khi phát hiện Trainer hoặc Trainee không hoàn thành đánh giá sau 24h.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% các buổi học có cấu hình đánh giá tự động mở luồng đánh giá ngay sau khi buổi học kết thúc.
- **SC-002**: Trainer và Trainee có thể hoàn thành việc gửi phiếu đánh giá trong vòng dưới 90 giây thông qua giao diện trực quan.
- **SC-003**: 100% điểm trung bình và báo cáo thống kê tiêu chí được tính toán chính xác ngay khi có phiếu đánh giá mới được gửi.
- **SC-004**: 100% các trường hợp Trainer/Trainee quá hạn 24h chưa hoàn thành đánh giá được quét và tạo biên bản vi phạm chính xác.
- **SC-005**: 0% trường hợp dữ liệu đánh giá bị trùng lặp hoặc lộ danh tính khi học viên chọn chế độ gửi ẩn danh (`is_anonymous = true`).
