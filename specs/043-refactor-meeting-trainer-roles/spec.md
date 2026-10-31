# Feature Specification: Tách Biệt Vai Trò Trainer & Trainee Trong Quản Lý Buổi Học (Meeting Participant Roles Refactor)

**Feature Branch**: `043-refactor-meeting-trainer-roles`  
**Created**: 2026-11-01  
**Status**: Draft  
**Input**: Yêu cầu refactor: Phân loại participant thành Trainer hoặc Trainee, form có 2 nơi nhập, bảng `meeting_participants` có thêm trường `role`, `created_by` chỉ mang ý nghĩa audit người tạo, Trainer là người phụ trách và có toàn quyền trong meeting.

---

## 🎯 Bối cảnh & Vấn đề Cần Giải Quyết

1. **Nhầm lẫn giữa `created_by` và `Trainer`**:
   - Hiện tại, hệ thống suy diễn Trainer của buổi học dựa trên `meeting.created_by` (người bấm tạo meeting).
   - Trong thực tế quản lý CLB/Lab: Admin hoặc Ban điều hành (Leader) thường là người lên lịch tạo buổi học thay cho các Trainer/Mentor đứng lớp. `created_by` chỉ nên mang ý nghĩa audit log (ai là người tạo dữ liệu).
   - Trainer là người hướng dẫn chuyên môn thực tế, có thể là một hoặc nhiều thành viên khác, và Trainer phải có toàn quyền điều hành meeting đó (điểm danh, đổi trạng thái, nộp đánh giá tổng thể, đánh giá học viên).
2. **Thiếu trường phân loại trong bảng `meeting_participants`**:
   - Hiện tại bảng `meeting_participants` chỉ lưu `status` (`ParticipantStatus`), gom chung tất cả người tham gia vào một mảng, không phân biệt ai là người dạy (Trainer), ai là người học (Trainee).
3. **Form tạo/sửa buổi họp chưa có khu vực chọn Trainer riêng**:
   - Form hiện tại chỉ có một ô chọn `user_ids` chung, không cho phép chỉ định ai là Trainer phụ trách buổi học.
4. **Hệ quả dây chuyền đến các luồng nghiệp vụ khác**:
   - Trainee đánh giá nhầm người tạo meeting thay vì Trainer thật.
   - Job phạt vi phạm và Scanner nhắc nhở đánh giá chỉ quét `created_by`, khiến Trainer thực tế không nhận được thông báo nhắc nhở và không nộp được đánh giá.

---

## 👥 User Scenarios & Acceptance Criteria

### User Story 1 - Phân loại Trainer và Trainee trên Form tạo/sửa buổi học (Priority: P1) 🎯 MVP

Là một người tạo buổi họp (Admin / Leader / Member), tôi muốn form có 2 khu vực nhập riêng biệt: một nơi chọn **Trainer phụ trách** và một nơi chọn **Trainees tham gia**, để buổi học phản ánh chính xác phân công nhân sự.

**Why this priority**: Cốt lõi của việc nhập liệu chuẩn xác ngay từ khâu khởi tạo buổi họp.

**Independent Test**:
- Mở modal Tạo/Sửa buổi học:
  - Chọn User A làm Trainer.
  - Chọn User B, C làm Trainee (có thể chọn qua Team hoặc User cá nhân).
- Bấm Lưu.
- Bảng `meeting_participants` lưu User A với `role = 'TRAINER'`, User B & C với `role = 'TRAINEE'`.

**Acceptance Scenarios**:
1. **Given** form tạo meeting, **When** người dùng chọn Trainer ở ô Trainer và chọn học viên ở ô Trainee, **Then** hệ thống lưu chính xác vai trò tương ứng vào bảng `meeting_participants`.
2. **Given** một user vô tình được chọn ở cả ô Trainer và Trainee, **Then** hệ thống ưu tiên vai trò `TRAINER` và tự động loại bỏ khỏi danh sách `TRAINEE` để tránh trùng lặp.
3. **Given** buổi meeting là buổi tự học nhóm / sinh hoạt tự do không có người giảng dạy, **When** người dùng để trống ô Trainer (`trainer_ids = []`), **Then** hệ thống vẫn cho phép tạo meeting thành công mà không hiển thị lỗi bắt buộc Trainer. Người tạo meeting (`created_by`) hoặc Admin/Leader sẽ giữ quyền điều hành.

---

### User Story 2 - Trao toàn quyền điều hành Meeting cho Trainer (Priority: P2)

Là một Trainer được phân công đứng lớp (dù không phải là người tạo meeting), tôi muốn có toàn quyền trong buổi họp đó: xem danh sách, điểm danh cho học viên, đổi trạng thái tham gia, nộp Đánh giá tổng thể buổi học và Đánh giá học viên.

**Why this priority**: Đảm bảo phân quyền chính xác theo vai trò nghiệp vụ thực tế.

**Independent Test**:
- User A (Admin) tạo meeting và gán User B làm Trainer.
- User B đăng nhập vào hệ thống:
  - Có đầy đủ quyền sửa trạng thái điểm danh cho học viên trong meeting.
  - Có quyền mở modal nộp Đánh giá tổng thể (`MeetingOverallEvaluation`).
  - Có quyền đánh giá từng học viên (`SubmitTrainerEvaluationUseCase`).

**Acceptance Scenarios**:
1. **Given** người dùng là Trainer trong meeting (`participant.role == 'TRAINER'`), **When** thực hiện các thao tác quản lý buổi học, **Then** hệ thống cho phép thực hiện mà không bị chặn lỗi 403.
2. **Given** người tạo meeting (`created_by`), **Then** vẫn giữ quyền quản trị cơ bản (audit/chỉnh sửa meeting).

---

### User Story 3 - Tách biệt 2 Bảng Giảng viên & Học viên trên UI và Đồng bộ luồng Đánh giá / Nhắc nhở (Priority: P3)

Là một người dùng xem chi tiết buổi học (học viên, giảng viên hoặc ban quản lý), tôi muốn danh sách người tham gia được chia thành **2 bảng riêng biệt** (Bảng Trainer và Bảng Trainee), và học viên có thể lựa chọn đánh giá đúng Trainer mong muốn khi buổi học có nhiều Trainer phụ trách.

**Why this priority**: Trực quan hóa cấu trúc lớp học, tách biệt rõ ràng khu vực quản lý giảng viên và học viên, đồng thời hỗ trợ lớp học có nhiều Trainer cùng phụ trách mà không cần chỉ định Trainer đại diện chính.

**Acceptance Scenarios**:
1. **Given** màn hình chi tiết buổi học (`MeetingParticipantsTab`) hoặc modal danh sách (`ParticipantListModal`), **Then** hệ thống hiển thị **2 bảng riêng biệt**:
   - **Bảng Trainer**: Danh sách các Trainer phụ trách buổi học, trạng thái tham gia, check-in, check-out, ảnh quẹt thẻ và điểm đánh giá trung bình. Bảng này không có nút chấm điểm học viên.
   - **Bảng Trainee**: Danh sách học viên tham gia, trạng thái tham gia, check-in, check-out, ảnh quẹt thẻ, trạng thái đã gửi đánh giá Trainer, nút sửa trạng thái điểm danh và nút đánh giá học viên dành cho Trainer.
2. **Given** buổi học có nhiều Trainer phụ trách, **When** học viên bấm nộp đánh giá Trainer (`TraineeEvaluationModal`), **Then** modal cung cấp danh sách lựa chọn Trainer muốn đánh giá (hoặc đánh giá lần lượt từng Trainer).
3. **Given** buổi học không có Trainer (`trainers.length === 0`), **Then** bảng Trainer hiển thị thông báo nhẹ (buổi tự học nhóm) và ẩn luồng đánh giá giảng viên.
4. **Given** scanner nhắc nhở đánh giá (`MeetingEvaluationTaskScanner`), **Then** hệ thống quét toàn bộ các thành viên có `role == 'TRAINER'` trong meeting để nhắc nộp đánh giá tổng thể và đánh giá học viên.

---

## 📋 Functional Requirements

- **FR-001**: Bổ sung Enum `ParticipantRole` gồm 2 giá trị `TRAINER` và `TRAINEE` trong `app/meeting/domain/value_objects.py`.
- **FR-002**: Thêm cột `role VARCHAR(50) NOT NULL DEFAULT 'TRAINEE'` vào bảng `meeting_participants` qua Alembic migration, kèm logic backfill gán vai trò `TRAINER` cho người tạo buổi học đối với dữ liệu cũ.
- **FR-003**: Cập nhật entity `MeetingParticipant` có trường `role: ParticipantRole = ParticipantRole.TRAINEE`.
- **FR-004**: Bổ sung các helper methods trong `Meeting` entity hỗ trợ nhiều Trainer bình đẳng (không cần Trainer đại diện chính):
  - `trainers`: danh sách participants có `role == ParticipantRole.TRAINER`.
  - `trainees`: danh sách participants có `role == ParticipantRole.TRAINEE`.
  - `is_trainer(user_id: int) -> bool`: kiểm tra user có phải một trong các trainer của meeting.
  - `is_trainee(user_id: int) -> bool`: kiểm tra user có phải trainee của meeting.
- **FR-005**: Cập nhật DTO `MeetingCreate` và `MeetingUpdate`:
  - `trainer_ids: list[int] = Field(default_factory=list)`: danh sách ID của các Trainer phụ trách (cho phép rỗng hoặc nhiều Trainer).
  - `trainee_ids: list[int] = Field(default_factory=list)`: danh sách ID của Trainee tham gia.
  - Trường hợp buổi meeting không có Trainer (`trainer_ids` rỗng), hệ thống tự động vô hiệu hóa luồng đánh giá giảng viên (`TRAINEE_TO_TRAINER`) và không áp dụng phạt đánh giá đối với Trainer. Người tạo buổi học (`created_by`) hoặc Admin/Leader giữ quyền điều hành.
- **FR-006**: Cập nhật `create_meeting_use_case.py` và `update_meeting_use_case.py` để phân bổ participants theo đúng role khi lưu database.
- **FR-007**: Cập nhật `check_meeting_ownership` và `check_meeting_evaluation_permission` trong `dependencies.py` cấp toàn quyền cho `meeting.is_trainer(current_user.id)`. Bất kỳ Trainer nào trong meeting đều có quyền điểm danh và nộp đánh giá tổng thể.
- **FR-008**: Cập nhật giao diện `MeetingModal.tsx` gồm 2 ô chọn rõ ràng: Ô chọn Trainer(s) (cho phép chọn nhiều) và Ô chọn Trainee(s) (kèm chọn nhanh theo Team).
- **FR-009**: Tách giao diện danh sách người tham gia (`MeetingParticipantsTab.tsx`, `ParticipantListModal.tsx`) thành **2 bảng riêng biệt**:
  - **Bảng 1: TrainerTable**: Hiển thị danh sách Trainer, trạng thái điểm danh, ảnh quẹt thẻ, điểm đánh giá trung bình.
  - **Bảng 2: TraineeTable**: Hiển thị danh sách Trainee, trạng thái điểm danh, ảnh quẹt thẻ, trạng thái gửi đánh giá, nút thao tác đổi trạng thái và nút đánh giá học viên.
- **FR-010**: Cập nhật `TraineeEvaluationModal.tsx` hỗ trợ chọn Trainer muốn đánh giá khi meeting có nhiều Trainer phụ trách.
- **FR-011**: Cập nhật `MeetingEvaluationTaskScanner` và `CheckEvaluationDeadlineJobUseCase` quét danh sách `meeting.trainers` thay vì `meeting.created_by`.

---

## 🎯 Success Criteria

- **SC-001**: 100% các buổi học mới tạo đều phân định rõ ràng Trainer và Trainee trong bảng `meeting_participants`.
- **SC-002**: Trainer được phân công có toàn quyền quản lý, điểm danh và đánh giá buổi học ngay cả khi không phải là người bấm nút tạo meeting.
- **SC-003**: Dữ liệu lịch sử cũ được migration an toàn, không làm hỏng các buổi họp đã diễn ra.
- **SC-004**: 100% test suite meeting và reminder đều vượt qua kiểm thử regression.
