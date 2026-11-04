# Feature Specification: Chuẩn hóa Hợp đồng Định danh & Đánh giá Meeting Full Stack

**Feature Branch**: `045-unify-meeting-evaluation-contracts`  
**Created**: 2026-11-04  
**Status**: Ready for Planning  
**Input**: Chuẩn hóa toàn diện định danh Người dùng (`user_id`) và Thành viên tham gia (`participant_id`) trong luồng Đánh giá Buổi học (Meeting Evaluation) giữa Backend và Frontend; đảm bảo Backend chỉ chấp nhận `user_id` hợp lệ và Frontend gửi chính xác dữ liệu theo hợp đồng.

---

## 🎯 Bối cảnh & Vấn đề Cốt lõi

Trong hệ thống quản lý buổi học và đánh giá hai chiều (Meeting & Evaluation):
1. **Sự nhập nhằng giữa hai loại định danh**:
   - `user_id`: Định danh tài khoản hệ thống của người dùng (tồn tại xuyên suốt các buổi học).
   - `participant_id`: Định danh bản ghi tham gia một buổi học cụ thể (chỉ có giá trị trong phạm vi buổi học đó).
2. **Bất đồng bộ trong dữ liệu trả về của Backend**:
   - Dữ liệu danh sách buổi học (List View) biểu diễn danh sách Trainer dưới dạng tham chiếu người dùng (với thuộc tính `id` là `user_id`).
   - Dữ liệu chi tiết buổi học (Detail View) biểu diễn danh sách Trainer dưới dạng bản ghi tham gia (với thuộc tính `id` là `participant_id`, còn `user_id` mới là ID của người dùng).
3. **Hậu quả**:
   - Giao diện người dùng (Frontend) có thể lấy nhầm `participant_id` (ví dụ `2436`) để gửi vào trường `target_user_id`, khiến Backend từ chối hợp lệ với thông báo *"Người được đánh giá không phải là Trainer của buổi học này"* (vì `user_id` thực tế là `1`).
   - Giao diện phải sử dụng các hàm suy đoán tạm bợ và kiểm tra vai trò người dùng bị lặp lại ở nhiều màn hình.
   - Backend cần giữ vững nguyên tắc Fail-Fast: chỉ chấp nhận `user_id` chuẩn, không thỏa hiệp với các định danh sai lệch, đồng thời chuẩn hóa rõ ràng các DTO trả về cho Client.

---

## 👥 User Scenarios & Testing *(mandatory)*

### User Story 1 - Học viên (Trainee) gửi đánh giá chính xác cho Giảng viên (Trainer) (Priority: P1)

Là một Học viên đã tham gia buổi học, tôi muốn đánh giá Trainer phụ trách buổi học theo 4 tiêu chí chuẩn hóa và gửi nhận xét (công khai hoặc ẩn danh), để hệ thống ghi nhận chính xác kết quả đánh giá cho đúng Trainer mà không gặp lỗi từ chối định danh.

**Why this priority**: Đây là luồng nghiệp vụ cốt lõi của tính năng Đánh giá hai chiều đang bị lỗi nghiêm trọng khi học viên thực hiện gửi đánh giá.

**Independent Test**:
- Đăng nhập bằng tài khoản Trainee tham gia buổi học #184 (hoặc buổi học bất kỳ có Trainer).
- Mở modal đánh giá Trainer, chọn điểm và nhập nhận xét, nhấn gửi.
- Hệ thống ghi nhận thành công, trạng thái hiển thị đã đánh giá, không xuất hiện lỗi xác thực 400.

**Acceptance Scenarios**:
1. **Given** một buổi học có 1 Trainer (`user_id = 1`) và cổng đánh giá đang mở, **When** Trainee mở modal đánh giá và nhấn gửi, **Then** hệ thống tự động xác định người nhận đánh giá là `user_id = 1` và lưu trữ đánh giá thành công.
2. **Given** một buổi học có nhiều Trainers, **When** Trainee mở modal đánh giá, **Then** giao diện hiển thị danh sách Trainers để lựa chọn, và khi gửi, hệ thống gửi chính xác `user_id` của Trainer được chọn.
3. **Given** yêu cầu đánh giá gửi lên hệ thống, **When** mã định danh `target_user_id` không khớp với bất kỳ `user_id` nào trong danh sách Trainers của buổi học, **Then** Backend từ chối với thông báo rõ ràng *"Người được đánh giá không phải là Trainer của buổi học này"*.

---

### User Story 2 - Nhất quán Hợp đồng Dữ liệu Định danh giữa Backend & Frontend (Priority: P2)

Là một Lập trình viên Full Stack, tôi muốn các API trả về của Backend phân định rành mạch giữa thông tin người dùng (`user_id`, tên, avatar) và thông tin tham gia buổi họp (`participant_id`, trạng thái điểm danh, thời gian check-in), để Frontend không bao giờ bị nhầm lẫn giữa hai loại khóa chính này.

**Why this priority**: Ngăn ngừa tận gốc nguyên nhân gây lỗi nhập nhằng mã định danh trong tương lai khi phát triển thêm các tính năng liên quan đến buổi họp.

**Independent Test**:
- Kiểm tra các endpoint lấy danh sách và chi tiết buổi học: Các trường đại diện cho ID người dùng luôn được đặt tên hoặc ánh xạ nhất quán (`user_id` hoặc cấu trúc `UserRef`).
- Kiểm tra mã nguồn Frontend: Không sử dụng các hàm fallback đoán trường (`id ?? user_id`), các component chỉ nhận View Model chuẩn `EvaluatableTrainer`.

**Acceptance Scenarios**:
1. **Given** Client gọi API chi tiết buổi học, **When** nhận dữ liệu `trainers` và `trainees`, **Then** mỗi đối tượng đều có `user_id` chỉ định danh người dùng và `id` chỉ bản ghi tham dự một cách minh bạch.
2. **Given** Frontend cần lấy danh sách Trainer để hiển thị và đánh giá, **When** chuyển đổi sang View Model, **Then** View Model chỉ chứa `userId`, `name`, `avatarUrl`, loại bỏ hoàn toàn các trường thừa của buổi học.

---

### User Story 3 - Tập trung hóa Logic Phân quyền & Trạng thái Buổi học trên Frontend (Priority: P3)

Là một người dùng (Trainer hoặc Trainee), tôi muốn giao diện hiển thị đúng các nút chức năng (Đánh giá Trainer, Điểm danh nhanh, Xem kết quả) tương ứng với vai trò thực tế của mình mà không bị sai lệch hoặc chớp nháy giao diện.

**Why this priority**: Loại bỏ trùng lặp mã nguồn (DRY), giúp trải nghiệm người dùng nhất quán và dễ bảo trì khi có thay đổi về quy tắc nghiệp vụ.

**Independent Test**:
- Kiểm tra 4 vị trí giao diện (`MeetingHeroHeader`, `MeetingParticipantsTab`, `MeetingTraineeEvaluationBanner`, `MeetingBatchCheckInBanner`): Cùng dùng chung một nguồn kiểm tra quyền duy nhất.
- Đăng nhập lần lượt với Admin, Trainer của buổi học, Trainee của buổi học, và người ngoài để xác minh các nút hiển thị chính xác.

**Acceptance Scenarios**:
1. **Given** người dùng là Trainer hoặc Admin, **When** xem trang buổi học, **Then** hệ thống hiển thị nút Điểm danh hàng loạt và công cụ đánh giá dành cho Trainer.
2. **Given** người dùng là Trainee, **When** buổi học mở cổng đánh giá, **Then** hiển thị banner và nút mở modal đánh giá Trainer.

---

### Edge Cases

- **Buổi học không có Trainer nào**: Hệ thống từ chối mở modal hoặc gửi đánh giá với thông báo *"Buổi học này không có Trainer phụ trách để đánh giá"*.
- **Người dùng cố tình gửi `participant_id` vào trường `target_user_id`**: Backend từ chối ngay lập tức theo nguyên tắc Fail-Fast, không tự động fallback ngầm để bảo đảm tính toàn vẹn dữ liệu.
- **Buổi học đã kết thúc quá 24 giờ**: Cổng đánh giá tự động đóng, cả Backend và Frontend đều chặn không cho gửi đánh giá mới.
- **Học viên cập nhật lại đánh giá đã gửi**: Hệ thống cho phép cập nhật điểm và nhận xét của bản ghi đánh giá hiện có thay vì tạo bản ghi trùng lặp.

---

## 📋 Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Backend MUST chỉ chấp nhận `target_user_id` là mã định danh người dùng (`user_id`) hợp lệ của một Trainer thuộc buổi học khi tiếp nhận đánh giá từ Trainee.
- **FR-002**: Backend MUST tự động phân giải `target_user_id` thành `user_id` của Trainer duy nhất nếu buổi học chỉ có đúng 1 Trainer và client không truyền `target_user_id`.
- **FR-003**: Backend MUST từ chối yêu cầu đánh giá với mã lỗi 400 và thông điệp rõ ràng nếu `target_user_id` không khớp với `user_id` của bất kỳ Trainer nào trong buổi học.
- **FR-004**: Backend Read Model DTOs MUST cung cấp đầy đủ và minh bạch cả `user_id` lẫn `id` (participant ID) trong danh sách người tham gia buổi học, đảm bảo không có trường nào bị `null` ngoài ý muốn.
- **FR-005**: Frontend MUST đóng gói dữ liệu Trainer dùng cho mục đích đánh giá thành View Model chuẩn (`EvaluatableTrainer`), tách biệt hoàn toàn khỏi Model bản ghi điểm danh.
- **FR-006**: Frontend MUST gửi chính xác `user_id` vào thuộc tính `target_user_id` trong payload của API gửi đánh giá.
- **FR-007**: Frontend MUST quản lý quyền hạn và vai trò đối với buổi học (`isTrainer`, `isTrainee`, `canEvaluateTrainer`, `canEvaluateTrainee`) qua một Single Source of Truth duy nhất (`useMeetingPermissions`).
- **FR-008**: Frontend MUST loại bỏ hoàn toàn các kiểu dữ liệu lỏng lẻo (`any`) và các hàm phỏng đoán mã định danh (`t.user_id ?? t.id`) tại các component UI.

---

### Key Entities *(include if feature involves data)*

- **User**: Thực thể người dùng hệ thống (chứa `id`, `name`, `avatar_url`, `roles`).
- **Meeting**: Thực thể buổi học (Aggregate Root quản lý thời gian, trạng thái đánh giá, danh sách người tham gia).
- **MeetingParticipant**: Bản ghi liên kết người dùng với buổi học cụ thể (chứa `id`, `meeting_id`, `user_id`, `role`, `status`, `check_in_at`).
- **MeetingEvaluation**: Thực thể đánh giá (chứa `meeting_id`, `reviewer_id`, `target_user_id`, `evaluation_type`, `scores`, `feedback_text`, `is_anonymous`).

---

## 🎯 Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% các lượt gửi đánh giá Trainer từ giao diện người dùng gửi đúng `user_id` và được Backend tiếp nhận thành công (0 lỗi 400 do sai lệch định danh).
- **SC-002**: Xóa bỏ hoàn toàn 100% các đoạn code kiểm tra trùng lặp logic vai trò ở 4 component giao diện chính.
- **SC-003**: 0 lỗi TypeScript (`npx tsc --noEmit` pass tuyệt đối) và 100% các unit test liên quan đến Meeting & Evaluation trên Backend pass.
- **SC-004**: Thời gian phản hồi và xử lý đánh giá hoàn tất trong dưới 500ms đối với thao tác của người dùng.

---

## 📌 Assumptions

- Bảng `users` là nguồn chân lý duy nhất cho tài khoản người dùng (`users.id`).
- Bảng `meeting_participants` lưu trữ thông tin tham gia theo từng buổi học, có khóa ngoại trỏ về `users.id`.
- Hợp đồng API `POST /api/v1/meetings/{id}/evaluations/trainee` giữ nguyên cấu trúc payload với trường `target_user_id` đại diện cho `users.id`.
