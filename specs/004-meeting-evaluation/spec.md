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

### Session 2026-10-11
- Q: Khi Trainer đánh giá tổng thể meeting thay vì từng cá nhân, trường đối tượng mục tiêu (`target_user_id`) và phân loại đánh giá của Trainer sẽ được lưu trữ và biểu diễn như thế nào trong mô hình dữ liệu? → A: Tạo một bảng riêng biệt `MeetingOverallEvaluation` dành riêng cho việc Trainer đánh giá meeting, tách biệt hoàn toàn với bảng đánh giá người dùng (`MeetingEvaluation`).
- Q: Điều kiện hoàn thành nghĩa vụ đánh giá và cơ chế phạt vi phạm (`Violation`) của Trainer sẽ thay đổi như thế nào sau khi chuyển sang đánh giá buổi học 1 - 1? → A: Hoàn tất khi có 01 bản ghi `MeetingOverallEvaluation` từ Trainer trong 24h; nếu chưa gửi thì bị phạt 01 vi phạm (`Violation`).
- Q: Về phía các Trainee tham gia buổi học, ai có quyền được xem nội dung đánh giá và điểm số buổi học do Trainer gửi (`MeetingOverallEvaluation`), và điều kiện để được xem là gì? → A: Công khai ngay cho tất cả Trainee tham gia lớp xem ngay khi Trainer gửi đánh giá, không phụ thuộc vào việc Trainee đã hoàn thành đánh giá Trainer hay chưa.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Trainer tạo buổi học và cấu hình cơ chế đánh giá 2 chiều (Priority: P1)

Trainer (người tạo meeting/lớp học) tạo một buổi học mới với danh sách Trainee tham gia. Buổi học có tùy chọn bật cơ chế đánh giá bắt buộc 2 chiều (Trainer đánh giá toàn diện buổi học theo quan hệ 1 - 1 và Trainee đánh giá cá nhân Trainer) sau khi buổi học kết thúc với thời hạn đánh giá xác định (mặc định 24h).

**Why this priority**: Đây là điểm khởi đầu cho toàn bộ vòng đời của buổi học có đánh giá, thiết lập cấu hình đánh giá cho buổi học và người chịu trách nhiệm đánh giá.

**Independent Test**: Trainer tạo một buổi học với danh sách 3 Trainee, bật cờ yêu cầu đánh giá 2 chiều (`enable_evaluation = true`). Kiểm tra buổi học được lưu thành công và sẵn sàng chuyển sang trạng thái chờ đánh giá khi lớp học kết thúc.

**Acceptance Scenarios**:

1. **Given** Trainer đang ở giao diện tạo Meeting/Buổi học, **When** Trainer nhập thông tin (tiêu đề, thời gian, danh sách Trainee) và kích hoạt chế độ "Đánh giá 2 chiều", **Then** hệ thống khởi tạo buổi học với cấu hình đánh giá tương ứng và hạn chót đánh giá (24h sau kết thúc).
2. **Given** buổi học đã được tạo thành công, **When** Trainee xem chi tiết lịch học, **Then** Trainee thấy thông tin lớp học cùng thông báo về nghĩa vụ đánh giá Trainer và hạn chót hoàn thành trong 24h sau buổi học.

---

### User Story 2 - Trainer đánh giá tổng thể buổi học (Quan hệ 1 - 1) sau buổi học (Priority: P1)

Sau khi buổi học kết thúc (hoặc chuyển sang trạng thái hoàn thành), thay vì đánh giá từng học viên riêng lẻ, Trainer chỉ cần truy cập vào buổi học để gửi 01 phiếu đánh giá tổng thể cho chính buổi học đó (`MeetingOverallEvaluation`) theo bộ 4 tiêu chí chuẩn hóa giữ nguyên của hệ thống (Chuyên cần & Tác phong, Mức độ Tương tác & Đóng góp, Mức độ Tiếp thu & Hiểu bài, Mức độ Chuẩn bị bài trước buổi học) kèm nhận xét chung.

**Why this priority**: Tinh gọn quy trình nghiệp vụ cho Trainer, giúp tiết kiệm thời gian đánh giá trong khi vẫn đảm bảo theo dõi chất lượng toàn diện của cả buổi học.

**Independent Test**: Trainer mở chi tiết buổi học đã hoàn thành, điền 01 biểu mẫu đánh giá tổng thể meeting với 4 tiêu chí chuẩn và lời nhận xét chung, rồi gửi thành công. Kiểm tra hệ thống lưu vào bảng `MeetingOverallEvaluation` và ghi nhận Trainer đã hoàn thành nghĩa vụ.

**Acceptance Scenarios**:

1. **Given** buổi học có bật đánh giá đã hoàn thành, **When** Trainer mở trang chi tiết buổi học, **Then** hệ thống hiển thị biểu mẫu đánh giá tổng thể buổi học kèm trạng thái đánh giá (Chưa đánh giá / Đã đánh giá).
2. **Given** Trainer nhập điểm đánh giá theo thang điểm chuẩn (1-5 sao) cho 4 tiêu chí cùng nhận xét tổng thể buổi học, **When** Trainer bấm gửi đánh giá, **Then** hệ thống ghi nhận phiếu đánh giá vào bảng `MeetingOverallEvaluation`, cập nhật trạng thái Trainer là đã hoàn thành đánh giá buổi học đó.
3. **Given** Trainer đã gửi đánh giá tổng thể buổi học thành công, **When** Trainer thử gửi lại, **Then** hệ thống ngăn chặn gửi trùng lặp do quan hệ 1 - 1 giữa Meeting và MeetingOverallEvaluation.

---

### User Story 3 - Trainee đánh giá Trainer với tùy chọn ẩn danh (Priority: P1)

Trainee sau khi tham gia lớp học có trách nhiệm gửi phản hồi/đánh giá trực tiếp cho Trainer theo bộ 4 tiêu chí giảng dạy chuẩn hóa (Chất lượng Nội dung bài học, Phương pháp Giảng dạy & Hỗ trợ, Không khí Lớp học & Sự tương tác, Giá trị Thu nhận & Tính ứng dụng) kèm góp ý cải thiện. Trainee có quyền chủ động tick chọn "Gửi ẩn danh".

**Why this priority**: Giúp nâng cao chất lượng giảng dạy thông qua phản hồi thực tế từ học viên dành cho Trainer, đảm bảo tính minh bạch và 2 chiều của môi trường giáo dục.

**Independent Test**: Trainee đăng nhập vào hệ thống, truy cập buổi học vừa tham gia, điền biểu mẫu đánh giá Trainer, chọn ẩn danh hoặc không, và gửi thành công.

**Acceptance Scenarios**:

1. **Given** Trainee đã tham gia buổi học và chưa thực hiện đánh giá Trainer, **When** Trainee truy cập trang chi tiết buổi học hoặc nhận thông báo nhắc nhở, **Then** hệ thống hiển thị biểu mẫu đánh giá Trainer với tùy chọn "Gửi ẩn danh".
2. **Given** Trainee chấm điểm 4 tiêu chí chất lượng, nhập ý kiến đóng góp và chọn "Gửi ẩn danh", **When** Trainee nhấn gửi đánh giá, **Then** hệ thống lưu đầy đủ ID người đánh giá trong DB (`MeetingEvaluation`) nhưng mask/ẩn danh tính đối với Trainer khi xem kết quả.
3. **Given** Trainer đã gửi đánh giá buổi học (`MeetingOverallEvaluation`), **When** bất kỳ Trainee nào tham gia lớp mở xem chi tiết buổi học, **Then** Trainee xem được kết quả đánh giá tổng thể và nhận xét của Trainer ngay lập tức mà không cần phụ thuộc vào việc Trainee đã gửi đánh giá hay chưa.

---

### User Story 4 - Báo cáo tổng hợp, chế tài hạn chót 24h và tự động tạo vi phạm (Priority: P2)

Trainer, Quản lý đào tạo (Admin) và Trainee có thể xem báo cáo tổng hợp kết quả đánh giá của buổi học: điểm đánh giá tổng thể buổi học của Trainer và điểm phản hồi trung bình từ Trainee. Tác vụ định kỳ tự động quét và tạo biên bản vi phạm cho Trainer (nếu chưa gửi đánh giá meeting) hoặc Trainee (nếu chưa gửi đánh giá Trainer) sau 24h.

**Why this priority**: Cung cấp bức tranh toàn diện về chất lượng buổi học và đảm bảo kỷ luật đánh giá bắt buộc 2 chiều bằng cơ chế vi phạm tự động.

**Independent Test**: Giả lập buổi học đã kết thúc quá 24h, kích hoạt tác vụ kiểm tra đánh giá và xác minh các trường hợp Trainer chưa gửi đánh giá meeting hoặc Trainee chưa đánh giá Trainer bị tự động tạo biên bản `Violation`.

**Acceptance Scenarios**:

1. **Given** Trainer xem phản hồi đánh giá từ các Trainee, **When** Trainer mở báo cáo, **Then** các đánh giá có `is_anonymous = true` hiển thị người gửi là "Học viên ẩn danh" mà không lộ thông tin cá nhân.
2. **Given** sau 24 giờ kể từ khi buổi học kết thúc mà Trainee chưa hoàn thành đánh giá Trainer, **When** tác vụ quét chạy, **Then** hệ thống tự động tạo 01 biên bản vi phạm ("Chưa hoàn thành đánh giá Trainer trong 24h") cho Trainee đó.
3. **Given** sau 24 giờ kể từ khi buổi học kết thúc mà Trainer chưa gửi 01 bản ghi `MeetingOverallEvaluation`, **When** tác vụ quét chạy, **Then** hệ thống tự động tạo 01 biên bản vi phạm ("Trainer chưa hoàn thành đánh giá buổi học trong 24h") cho Trainer.
4. **Given** Trainer đã gửi đánh giá tổng thể buổi học, **When** Trainee vào trang kết quả buổi học, **Then** Trainee xem được điểm số và lời nhận xét chung mà Trainer dành cho buổi học đó.

---

### Edge Cases

- **Trainee vắng mặt trong buổi học**: Đối với Trainee có trạng thái vắng mặt (`ABSENT_EXCUSED` hoặc `ABSENT_UNEXCUSED`), Trainee vắng mặt không có quyền đánh giá Trainer và không bị phạt vi phạm đánh giá.
- **Đánh giá trùng lặp**: Ràng buộc duy nhất:
  - Bảng `MeetingOverallEvaluation`: `UNIQUE(meeting_id)` đảm bảo mỗi buổi học chỉ có duy nhất 1 bản ghi đánh giá từ Trainer.
  - Bảng `MeetingEvaluation`: `UNIQUE(meeting_id, reviewer_id, target_user_id)` đảm bảo mỗi Trainee chỉ gửi duy nhất 1 phiếu đánh giá cho Trainer trong cùng một buổi học.
- **Buổi học bị hủy**: Khi buổi học bị hủy, toàn bộ quy trình và nghĩa vụ đánh giá cho buổi học đó tự động vô hiệu hóa.
- **Hết hạn đánh giá (Sau 24h)**: Trainer (nếu chưa có `MeetingOverallEvaluation`) hoặc Trainee (nếu chưa có `MeetingEvaluation` gửi Trainer) sau 24h chưa hoàn thành đánh giá thì hệ thống tự động tạo 01 biên bản vi phạm (`Violation`).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI cho phép Trainer bật/tắt tính năng "Đánh giá 2 chiều" (`enable_evaluation`) khi tạo hoặc cập nhật Buổi học.
- **FR-002**: Hệ thống PHẢI sử dụng bộ 4 tiêu chí cố định hệ thống (System Defaults) để Trainer đánh giá tổng thể Buổi học (`MeetingOverallEvaluation`) gồm:
  - *Chuyên cần & Tác phong* (Đúng giờ, tuân thủ nội quy).
  - *Mức độ Tương tác & Đóng góp* (Phát biểu, đặt câu hỏi, thảo luận nhóm).
  - *Mức độ Tiếp thu & Hiểu bài* (Nắm bắt kiến thức truyền tải).
  - *Mức độ Chuẩn bị bài trước buổi học* (Đọc trước tài liệu, chuẩn bị bài tập/môi trường trước khi lên lớp).
- **FR-003**: Hệ thống PHẢI sử dụng bộ 4 tiêu chí cố định hệ thống (System Defaults) để Trainee đánh giá cá nhân Trainer (`MeetingEvaluation`) gồm:
  - *Chất lượng Nội dung bài học* (Rõ ràng, thực tế, đúng tiến độ).
  - *Phương pháp Giảng dạy & Hỗ trợ của Trainer* (Nhiệt tình, giải đáp thỏa đáng, dễ hiểu).
  - *Không khí Lớp học & Sự tương tác* (Tạo động lực, lôi cuốn).
  - *Giá trị Thu nhận & Tính ứng dụng* (Mức độ tiếp thu kiến thức mới hữu ích).
- **FR-004**: Hệ thống PHẢI hỗ trợ thang điểm đánh giá chuẩn hóa từ 1 đến 5 sao cho từng tiêu chí trên cả hai biểu mẫu đánh giá.
- **FR-005**: Mỗi phiếu đánh giá (cả của Trainer và Trainee) PHẢI bao gồm điểm số theo 4 tiêu chí và phần nhận xét/góp ý dạng văn bản tự do (`feedback_text`).
- **FR-006**: Hệ thống PHẢI thiết lập quan hệ 1 - 1 giữa Buổi học (`Meeting`) và Đánh giá tổng thể buổi học (`MeetingOverallEvaluation`) do Trainer thực hiện. Trainer chỉ cần gửi đúng 1 phiếu đánh giá duy nhất cho toàn bộ buổi học thay vì đánh giá từng Trainee.
- **FR-007**: Hệ thống PHẢI cho phép Trainee gửi đánh giá cá nhân cho Trainer sau khi thời gian buổi học kết thúc và bản thân có tham gia (`JOINED` hoặc `COMPLETED`).
- **FR-008**: Hệ thống PHẢI cung cấp tùy chọn "Gửi ẩn danh" (`is_anonymous`) trên biểu mẫu đánh giá của Trainee. Hệ thống PHẢI lưu chính xác ID người đánh giá trong cơ sở dữ liệu (`MeetingEvaluation`) nhưng PHẢI che giấu thông tin danh tính khi hiển thị cho Trainer.
- **FR-009**: Hệ thống PHẢI áp dụng thời hạn đánh giá bắt buộc là **24 giờ** sau khi buổi học kết thúc cho cả Trainer và Trainee.
- **FR-010**: Tác vụ tự động PHẢI quét các buổi học sau 24 giờ kết thúc và tự động tạo biên bản vi phạm (`Violation`) cho Trainer (nếu chưa gửi `MeetingOverallEvaluation`) hoặc Trainee có tham gia nhưng chưa gửi đánh giá Trainer.
- **FR-011**: Hệ thống PHẢI hiển thị kết quả đánh giá tổng thể buổi học của Trainer công khai cho mọi Trainee tham gia ngay khi Trainer gửi đánh giá, không bắt buộc Trainee phải hoàn thành đánh giá trước.
- **FR-012**: Hệ thống PHẢI ngăn chặn việc gửi đánh giá trùng lặp thông qua ràng buộc duy nhất `UNIQUE(meeting_id)` cho bảng `MeetingOverallEvaluation` và `UNIQUE(meeting_id, reviewer_id, target_user_id)` cho bảng `MeetingEvaluation`.
- **FR-013**: Hệ thống PHẢI tính toán điểm đánh giá trung bình tổng thể và điểm trung bình theo từng tiêu chí cho cả buổi học (`MeetingOverallEvaluation`) và cho Trainer (`MeetingEvaluation`).
- **FR-014**: Hệ thống PHẢI tự động gửi thông báo nhắc nhở (qua Discord, Zalo hoặc Notification) cho Trainer và Trainee khi có buổi học cần hoàn thành đánh giá hoặc khi sắp hết hạn 24h.

---

### Key Entities *(include if feature involves data)*

- **Buổi học (`Meeting`)**: Được mở rộng thêm các thuộc tính: cờ kích hoạt đánh giá (`enable_evaluation`), hạn chót đánh giá (`evaluation_deadline`).
- **Đánh giá Tổng thể Buổi học (`MeetingOverallEvaluation`)**: Bảng riêng biệt đại diện cho đánh giá của Trainer dành cho buổi học (quan hệ 1 - 1 với `Meeting`). Thuộc tính: `id`, `meeting_id` (Unique, FK), `trainer_id` (FK), `scores` (JSONB gồm 4 tiêu chí), `average_score` (float), `general_feedback` (text), `created_at`.
- **Đánh giá Cá nhân Trainer từ Trainee (`MeetingEvaluation`)**: Đại diện cho phiếu đánh giá của Trainee dành cho Trainer. Thuộc tính: `id`, `meeting_id` (FK), `reviewer_id` (Trainee ID), `target_user_id` (Trainer ID), `is_anonymous` (boolean), `scores` (JSONB gồm 4 tiêu chí), `average_score` (float), `feedback_text` (text), `created_at`.
- **Biên bản Vi phạm (`Violation`)**: Thực thể thuộc domain Vi phạm, được tự động tạo khi phát hiện Trainer hoặc Trainee không hoàn thành đánh giá sau 24h.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% các buổi học có cấu hình đánh giá tự động mở luồng đánh giá ngay sau khi buổi học kết thúc.
- **SC-002**: Trainer chỉ cần gửi 01 biểu mẫu duy nhất cho toàn bộ buổi học và hoàn thành trong vòng dưới 60 giây.
- **SC-003**: 100% điểm trung bình và báo cáo thống kê tiêu chí được tính toán chính xác ngay khi có phiếu đánh giá mới được gửi.
- **SC-004**: 100% các trường hợp Trainer (chưa gửi `MeetingOverallEvaluation`) hoặc Trainee (chưa gửi `MeetingEvaluation`) quá hạn 24h được quét và tạo biên bản vi phạm chính xác.
- **SC-005**: 0% trường hợp dữ liệu đánh giá bị trùng lặp hoặc lộ danh tính khi học viên chọn chế độ gửi ẩn danh (`is_anonymous = true`).
