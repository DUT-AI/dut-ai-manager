# Feature Specification: Trainee Evaluation List in Meeting Detail

**Feature Branch**: `057-trainee-evaluation-list`

**Created**: 2026-11-10

**Status**: Draft

**Input**: User description: "Hiện tại ở UI chi tiết meeting tôi muốn xem được danh sách các Trainee đánh giá"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Xem danh sách và trạng thái đánh giá của từng Trainee trong buổi học (Priority: P1)

Là một Trainer (hoặc Quản trị viên/Mentor), khi xem trang chi tiết buổi học (`MeetingDetailPage`), tôi muốn nhìn thấy rõ ràng danh sách tất cả các Trainee tham gia buổi học và trạng thái đánh giá của từng học viên:
- Học viên nào đã hoàn thành đánh giá Trainer / buổi học (kèm mốc thời gian, điểm đánh giá trung bình nếu có quyền, và cờ ẩn danh).
- Học viên nào chưa đánh giá (kèm cảnh báo/nhắc nhở nếu buổi học đã kết thúc).
- Xem chi tiết nội dung đánh giá và tiêu chí điểm số của từng học viên trực tiếp từ danh sách nếu đánh giá không phải dạng ẩn danh.

**Why this priority**: Đây là mục tiêu cốt lõi của yêu cầu người dùng — giúp Trainer/Quản lý theo dõi tiến độ nộp đánh giá của học viên theo từng buổi học mà không cần phải đối chiếu thủ công hay suy đoán.

**Independent Test**:
- Vào trang chi tiết buổi học có bật tính năng đánh giá (`enable_evaluation = true`).
- Kiểm tra danh sách Trainee hiển thị cột trạng thái đánh giá rõ ràng (ví dụ: "Đã đánh giá" / "Chưa đánh giá") và có thể click xem chi tiết bài đánh giá của học viên đó.

**Acceptance Scenarios**:
1. **Given** một buổi học có `enable_evaluation = true` và có 10 Trainee (trong đó 6 người đã gửi đánh giá, 4 người chưa),
   **When** Trainer/Admin truy cập vào tab Người tham gia hoặc tab Báo cáo đánh giá,
   **Then** hệ thống hiển thị danh sách 10 học viên với nhãn/tag rõ ràng (6 học viên "Đã đánh giá", 4 học viên "Chưa đánh giá").
2. **Given** một học viên đã đánh giá ở chế độ công khai (không ẩn danh),
   **When** Trainer/Admin click vào mục xem chi tiết đánh giá của học viên đó,
   **Then** hệ thống hiển thị modal/drawer chi tiết các tiêu chí điểm số (Criteria Breakdown) và nội dung nhận xét (Feedback Text) mà học viên đó đã gửi.
3. **Given** một học viên đã đánh giá ở chế độ ẩn danh (`is_anonymous = true`),
   **When** Trainer/Admin xem danh sách,
   **Then** hệ thống hiển thị học viên đó "Đã đánh giá (Ẩn danh)" để xác nhận học viên đã hoàn thành trách nhiệm, nhưng bảo mật danh tính trong phần chi tiết nội dung ý kiến đóng góp theo đúng quy định ẩn danh.

---

### User Story 2 - Lọc danh sách Trainee theo trạng thái đánh giá (Priority: P2)

Là một Trainer/Quản lý, tôi muốn có bộ lọc nhanh giữa "Tất cả", "Đã đánh giá" và "Chưa đánh giá" trên danh sách Trainee để dễ dàng theo dõi số lượng học viên chưa gửi phản hồi.

**Why this priority**: Tăng tốc độ kiểm tra và nhắc nhở học viên khi chuẩn bị tổng kết buổi học.

**Independent Test**:
- Nhấn chọn filter "Chưa đánh giá", danh sách chỉ hiển thị các Trainee vắng mặt có phép hoặc chưa gửi bài đánh giá.
- Nhấn chọn "Đã đánh giá", danh sách chỉ hiển thị các Trainee đã gửi thành công.

**Acceptance Scenarios**:
1. **Given** danh sách Trainee trong buổi học,
   **When** người dùng chọn tab / bộ lọc "Chưa đánh giá",
   **Then** danh sách lọc đúng các học viên hợp lệ chưa nộp đánh giá, đồng thời hiển thị số lượng thống kê (ví dụ: `4/10 chưa đánh giá`).

---

### User Story 3 - Xem chi tiết ý kiến đóng góp theo từng Trainee trong Tab Báo cáo đánh giá (Priority: P3)

Trong tab "Báo cáo Đánh giá" (`MeetingEvaluationSummaryView`), ngoài biểu đồ thống kê chung, người dùng muốn có một bảng/danh sách phân đoạn riêng cho "Danh sách học viên đánh giá" để theo dõi trực quan từng bài đánh giá từ Trainee gửi cho Trainer.

**Why this priority**: Giúp tách biệt rõ ràng giữa góc nhìn "Người tham gia & Điểm danh" (Tab 1) và góc nhìn "Phân tích chất lượng giảng dạy từ Trainee" (Tab 2).

**Independent Test**:
- Chuyển sang Tab "Báo cáo Đánh giá", kiểm tra khu vực hiển thị danh sách Trainee đã đánh giá kèm điểm chi tiết và ý kiến phản hồi.

**Acceptance Scenarios**:
1. **Given** Tab "Báo cáo Đánh giá",
   **When** cuộn xuống danh mục đánh giá,
   **Then** hiển thị danh sách các Trainee đánh giá với thông tin người đánh giá (hoặc ẩn danh), đối tượng được đánh giá, điểm sao trung bình, và toàn văn nhận xét.

---

### Edge Cases

- **Buổi học không kích hoạt đánh giá (`enable_evaluation = false`)**: Ẩn toàn bộ cột/thông tin danh sách đánh giá Trainee để giao diện không bị thừa thông tin.
- **Học viên vắng mặt (có phép / không phép)**: Học viên vắng mặt không bắt buộc phải đánh giá, hệ thống cần đánh dấu trạng thái phù hợp (ví dụ: "Vắng mặt - Không áp dụng" hoặc loại khỏi chỉ số cần đánh giá).
- **Học viên đánh giá ẩn danh**: Hệ thống ghi nhận trạng thái đã hoàn thành của học viên để không nhắc nhở nhầm, nhưng khi hiển thị chi tiết nội dung feedback sẽ ẩn tên/avatar người gửi để bảo vệ tính ẩn danh của Trainee.
- **Trainee tự xem danh sách**: Nếu người đăng nhập là Trainee thường, họ chỉ xem được trạng thái đánh giá của chính mình, không được xem chi tiết điểm số hoặc bài đánh giá của các Trainee khác (tuân thủ RBAC).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI hiển thị danh sách toàn bộ Trainee của buổi học kèm trạng thái đánh giá tương ứng (`Đã gửi` / `Chưa gửi` / `Ẩn danh`).
- **FR-002**: Hệ thống PHẢI cho phép Trainer và Quản trị viên xem chi tiết điểm số các tiêu chí và nhận xét đóng góp của Trainee đối với buổi học/Trainer (với các đánh giá công khai).
- **FR-003**: Đối với các đánh giá ẩn danh (`is_anonymous = true`), hệ thống PHẢI xác nhận Trainee đã đánh giá thành công để tính tỷ lệ tham gia, nhưng KHÔNG ĐƯỢC tiết lộ nội dung đóng góp gắn liền với danh tính của học viên đó với Trainer.
- **FR-004**: Hệ thống PHẢI cung cấp bộ lọc hoặc phân loại nhanh danh sách Trainee theo trạng thái đánh giá (`Tất cả`, `Đã đánh giá`, `Chưa đánh giá`).
- **FR-005**: Giao diện PHẢI hiển thị thống kê tổng quan (ví dụ: `X/Y Trainee đã gửi đánh giá`) tại khu vực danh sách Trainee.
- **FR-006**: Nếu buổi học chưa bật tính năng đánh giá (`enable_evaluation = false`), hệ thống PHẢI ẩn các thành phần liên quan đến đánh giá Trainee.

### Key Entities

- **MeetingParticipant**: Đại diện cho học viên/giảng viên tham gia buổi học (`user_id`, `role: TRAINEE`, `status: PRESENT | ABSENT_...`).
- **MeetingEvaluation**: Bản ghi đánh giá buổi học/Trainer từ Trainee (`evaluation_type: TRAINEE_TO_TRAINER`, `reviewer_id`, `target_user_id`, `average_score`, `feedback_text`, `is_anonymous`).
- **MeetingEvaluationSummary**: Dữ liệu tổng hợp báo cáo đánh giá buổi học bao gồm danh sách chi tiết các đánh giá và điểm tiêu chí.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Trainer/Admin có thể xác định được danh sách học viên đã đánh giá và chưa đánh giá ngay trên màn hình chi tiết buổi học trong vòng 1 cú click.
- **SC-002**: 100% các đánh giá ẩn danh được bảo vệ danh tính, không rò rỉ thông tin cá nhân trong bảng nhận xét chi tiết.
- **SC-003**: Bộ lọc trạng thái đánh giá Trainee phản hồi tức thì (< 100ms) trên giao diện Client.
- **SC-004**: Không phát sinh lỗi biên dịch TypeScript (`tsc -b`) và đáp ứng chuẩn thiết kế UI/UX theo Hiến pháp dự án.

---

## Assumptions

- API backend hiện tại (`GET /api/v1/meetings/{id}/evaluations/summary`) đã cung cấp danh sách `evaluations` chứa thông tin các bài đánh giá của Trainee.
- Quyền truy cập chi tiết đánh giá tuân theo chính sách RBAC đã có của phân hệ Meeting (Trainer/Admin được xem tổng quan, Trainee chỉ xem bài đánh giá của chính mình).
