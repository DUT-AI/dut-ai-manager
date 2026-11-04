# Feature Specification: Tinh giản Đánh giá Meeting & Chuẩn hóa Kiến trúc Full Stack

**Feature Branch**: `046-harden-meeting-evaluation`  
**Created**: 2026-11-04  
**Status**: Ready for Planning  
**Input**: 
1. Tinh giản mô hình đánh giá: Bỏ hoàn toàn tính năng Trainer đánh giá từng Trainee cá nhân, Trainer chỉ đánh giá tổng thể buổi học (`MeetingOverallEvaluation`).
2. Siết chặt Domain Invariants: Chặn tự đánh giá (`reviewer_id == target_user_id`), kiểm tra vai trò hợp lệ.
3. Hoàn thiện toàn bộ Nhóm 2 (Code Quality, Hiến pháp & UX): Sửa lỗi Fake Optional theo Điều XIV, dọn sạch dead code và chuỗi không dấu trong Domain `MeetingParticipant`, tối ưu truy vấn lặp, và hiển thị Hạn chót đánh giá trên Frontend.
*(Lưu ý: Không thay đổi cơ chế hiển thị summary công khai hiện tại và không khóa cổng hết hạn đánh giá).*

---

## 🎯 Bối cảnh & Phạm vi Nghiệp vụ (Scope)

### Trong phạm vi thực hiện (In-Scope):
1. **Tinh giản mô hình Đánh giá (Eliminate Trainer-to-Trainee Individual Evaluation)**:
   - Trainer không còn phải chấm điểm từng học viên một. Bỏ hoàn toàn luồng đánh giá cá nhân `TRAINER_TO_TRAINEE`.
   - Trainer chỉ thực hiện **Đánh giá tổng thể toàn bộ buổi học** (`MeetingOverallEvaluation`) theo 4 tiêu chí chuẩn.
   - Trainee thực hiện **Đánh giá Trainer** phụ trách buổi học (`TRAINEE_TO_TRAINER`).
   - Frontend: Dọn dẹp các nút bấm "Chấm điểm học viên", cột trạng thái Trainer chấm trong bảng học viên, và component `TrainerEvaluationModal.tsx`.
   - Backend: Dọn dẹp/bỏ use case và endpoint `POST /{meeting_id}/evaluations/trainer`. Giải quyết triệt để bug phụ thuộc `created_by` do luồng này tạo ra.
2. **Siết chặt Domain Invariants (Hardening Invariants)**:
   - Chặn tuyệt đối hành vi tự đánh giá chính mình (`reviewer_id == target_user_id`).
   - Kiểm tra `target_user_id` bắt buộc phải là Trainer của buổi học trong `SubmitTraineeEvaluationUseCase`.
   - Kiểm tra người gửi đánh giá tổng thể trong `SubmitMeetingOverallEvaluationUseCase` bắt buộc phải là Trainer/Admin của buổi học.
3. **Chất lượng Code, Hiến pháp & Trải nghiệm (Code Quality, Constitution & UX)**:
   - **Tuân thủ Hiến pháp Điều XIV (No Fake Optionals)**: `GetMeetingEvaluationSummaryUseCase` chuyển `overall_eval_repo: MeetingOverallEvaluationRepository` thành tham số bắt buộc (non-nullable), loại bỏ `if self.overall_eval_repo:`.
   - **Xóa Dead Code & Chuỗi không dấu trong Domain**: Xóa bỏ method `check_in()` không dùng trong `MeetingParticipant`, sửa các chuỗi trong `check_out()` thành tiếng Việt có dấu chuẩn (`"Đã check-out"`, `"Check-out thành công"`).
   - **Tối ưu hóa Database Query**: Tránh query lặp lại `meeting` giữa Controller Permission Dependency và Use Case.
   - **Hiển thị Hạn chót trên Frontend**: Hiển thị rõ mốc thời gian hạn chót nộp đánh giá (`evaluation_deadline`) trên `MeetingHeroHeader` cho học viên nắm bắt.

### Ngoài phạm vi (Out-of-Scope):
- Không thay đổi cơ chế phân quyền xem summary công khai hiện tại.
- Không tự động đóng cổng / chặn nộp đánh giá khi quá hạn.

---

## 👥 User Scenarios & Testing *(mandatory)*

### User Story 1 - Tinh giản Trách nhiệm Đánh giá của Giảng viên (Priority: P1)

Là một Giảng viên (Trainer) phụ trách buổi học, tôi chỉ muốn gửi một phiếu đánh giá tổng thể duy nhất cho toàn bộ buổi học (về không khí lớp học, mức độ tiếp thu chung, chất lượng nội dung) thay vì phải mất thời gian chấm điểm từng học viên riêng lẻ.

**Why this priority**: Giảm tải áp lực nhập liệu cho Trainer, tập trung vào đánh giá chất lượng buổi học và đơn giản hóa kiến trúc hệ thống.

**Independent Test**:
- Đăng nhập với tài khoản Trainer, vào trang chi tiết buổi học.
- Bảng danh sách học viên không còn cột hay nút "Chấm điểm từng học viên".
- Trainer chỉ thấy nút "Trainer đánh giá buổi học" trên Header để gửi đánh giá tổng thể.
- Gửi đánh giá tổng thể thành công và hiển thị kết quả cho toàn bộ lớp.

**Acceptance Scenarios**:
1. **Given** một buổi học có kích hoạt đánh giá, **When** Trainer truy cập tab Thành viên, **Then** bảng danh sách học viên chỉ hiển thị thông tin điểm danh và trạng thái nộp bài, không hiển thị cột hay nút chấm điểm cá nhân.
2. **Given** Trainer gửi đánh giá tổng thể buổi học, **When** gửi thành công, **Then** hệ thống ghi nhận `MeetingOverallEvaluation` và hiển thị trên giao diện buổi học.

---

### User Story 2 - Siết chặt Invariants & Chống Tự Đánh giá (Priority: P2)

Là người quản trị hệ thống, tôi muốn đảm bảo các lượt đánh giá tuân thủ đúng quy tắc nghiệp vụ: người dùng không thể tự đánh giá chính mình, và học viên chỉ được đánh giá đúng Trainer của buổi học.

**Why this priority**: Đảm bảo tính toàn vẹn và độ tin cậy của dữ liệu đánh giá, ngăn ngừa gian lận hoặc gửi sai đối tượng.

**Independent Test**:
- Gọi API gửi đánh giá với `reviewer_id == target_user_id`: Hệ thống từ chối ngay lập tức với lỗi 400 *"Không thể tự đánh giá chính mình"*.
- Gửi đánh giá Trainer với `target_user_id` không phải Trainer của buổi học: Hệ thống từ chối với lỗi 400 *"Người được đánh giá không phải là Trainer của buổi học này"*.

**Acceptance Scenarios**:
1. **Given** một yêu cầu đánh giá từ Trainee, **When** `reviewer_id` trùng với `target_user_id`, **Then** hệ thống từ chối với thông báo lỗi rõ ràng.
2. **Given** một yêu cầu đánh giá tổng thể buổi học, **When** người gửi không phải là Trainer của buổi học, **Then** hệ thống từ chối cấp quyền.

---

### User Story 3 - Tuân thủ Hiến pháp & Trải nghiệm Người dùng (Priority: P3)

Là một Lập trình viên và Người dùng, tôi muốn hệ thống có mã nguồn trong sạch theo chuẩn Hiến pháp dự án (không Fake Optionals, không dead code), và giao diện hiển thị rõ hạn chót đánh giá để học viên biết thời điểm cần hoàn thành.

**Why this priority**: Nâng cao chất lượng mã nguồn, dễ bảo trì và cải thiện trải nghiệm người dùng trên giao diện.

**Independent Test**:
- Kiểm tra mã nguồn `GetMeetingEvaluationSummaryUseCase`: `overall_eval_repo` là non-nullable parameter.
- Kiểm tra Domain Entity `MeetingParticipant`: Không còn method rác `check_in()`, chuỗi tiếng Việt có dấu chuẩn.
- Xem `MeetingHeroHeader` trên giao diện: Thấy thông tin hạn chót đánh giá hiển thị rõ ràng bên cạnh trạng thái.

**Acceptance Scenarios**:
1. **Given** học viên truy cập trang buổi học có đánh giá, **When** xem thông tin trên Header, **Then** nhìn thấy mốc thời hạn chót gửi đánh giá rõ ràng.
2. **Given** toàn bộ test suite của backend, **When** chạy kiểm thử, **Then** đạt 100% pass với mã nguồn sạch chuẩn Hiến pháp.

---

### User Story 4 - Loại bỏ Dead Code, Component Mồ côi & Tinh giản Báo cáo Đánh giá (Priority: P4)

Là một Kỹ sư phần mềm và Người dùng, tôi muốn toàn bộ dead code, các component mồ côi không dùng đến, modal xem điểm cá nhân cũ, và khối báo cáo Trainer chấm lẻ học viên phải được dọn sạch dứt điểm để hệ thống nhẹ, dễ bảo trì và giao diện không bị gây hiểu nhầm.

**Why this priority**: Triệt tiêu nợ kỹ thuật (Technical Debt), loại bỏ mã rác và giúp giao diện Báo cáo Đánh giá phản ánh đúng 100% mô hình đánh giá mới.

**Independent Test**:
- Kiểm tra codebase Frontend: Không còn các file mồ côi `ParticipantListModal.tsx`, `ParticipantListTable.tsx`, `MeetingTraineeEvaluationBanner.tsx`, `MyEvaluationResultModal.tsx`.
- Giao diện Header & Banner: Không còn nút "Điểm của tôi" / "Xem Điểm của tôi".
- Tab Báo cáo Đánh giá: Không còn hiện ô trống "Trainer đánh giá Trainee" khi không có dữ liệu.
- Kiểm tra Backend: Xóa bỏ `SubmitTrainerEvaluationUseCase.py`, dọn dẹp các import thừa trong `evaluation_controller.py`.
- Toàn bộ backend test và frontend typecheck/build tiếp tục pass 100%.

**Acceptance Scenarios**:
1. **Given** người dùng truy cập chi tiết buổi học, **When** xem Header và tab Người tham gia, **Then** không còn nút bấm thừa "Điểm của tôi" / "Xem Điểm của tôi".
2. **Given** người dùng truy cập tab Báo cáo Đánh giá, **When** buổi học không có dữ liệu Trainer chấm lẻ cũ, **Then** giao diện chỉ hiển thị Đánh giá tổng thể của Giảng viên và Đánh giá của Học viên, không hiện khối trống gây hiểu nhầm.
3. **Given** môi trường phát triển, **When** chạy `npx tsc --noEmit` và `pytest`, **Then** 0 lỗi, mã nguồn sạch hoàn toàn không còn dead code.

---

## 📋 Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống MUST bỏ hoàn toàn tính năng Trainer đánh giá từng Trainee cá nhân (`TRAINER_TO_TRAINEE`).
- **FR-002**: Giao diện người dùng MUST loại bỏ nút bấm "Chấm điểm học viên", cột đánh giá cá nhân trong bảng học viên, và component `TrainerEvaluationModal.tsx`.
- **FR-003**: Hệ thống MUST giữ nguyên tính năng Trainer gửi Đánh giá tổng thể buổi học (`MeetingOverallEvaluation`) và tính năng Trainee gửi Đánh giá Trainer (`TRAINEE_TO_TRAINER`).
- **FR-004**: Backend MUST chặn tuyệt đối hành vi tự đánh giá chính mình (`reviewer_id == target_user_id`) trong `SubmitTraineeEvaluationUseCase`.
- **FR-005**: Backend MUST xác thực `trainer_id` trong `SubmitMeetingOverallEvaluationUseCase` bắt buộc phải là một Trainer thuộc buổi học hoặc Creator/Admin.
- **FR-006**: Tầng Application MUST loại bỏ Fake Optional trong constructor `GetMeetingEvaluationSummaryUseCase`, biến `overall_eval_repo: MeetingOverallEvaluationRepository` thành tham số bắt buộc theo Điều XIV của Hiến pháp.
- **FR-007**: Domain Entity `MeetingParticipant` MUST xóa bỏ method `check_in()` (dead code), và chuẩn hóa chuỗi phản hồi của `check_out()` thành tiếng Việt có dấu.
- **FR-008**: Frontend MUST hiển thị mốc thời gian hạn chót đánh giá (`evaluation_deadline`) trên `MeetingHeroHeader` khi buổi học kích hoạt tính năng đánh giá.
- **FR-009**: Frontend MUST xóa bỏ toàn bộ các file mồ côi không được sử dụng: `ParticipantListModal.tsx`, `ParticipantListTable.tsx`, `MeetingTraineeEvaluationBanner.tsx`.
- **FR-010**: Frontend MUST xóa bỏ modal tàn dư `MyEvaluationResultModal.tsx`, nút "Điểm của tôi" / "Xem Điểm của tôi" trên `MeetingHeroHeader`, `TraineeEvaluationCard`, `MeetingParticipantsTab`, `MeetingDetailPage`, cùng hook `useMyEvaluationResult` và service `meetingService.getMyEvaluationResult`.
- **FR-011**: Frontend MUST xóa bỏ service `submitTrainerEvaluation`, type `TrainerSubmitEvaluationPayload`, permission thừa `canEvaluateTrainee`, và prop thừa `isEnded` trong `ParticipantActionButtons.tsx`.
- **FR-012**: Backend MUST xóa bỏ `SubmitTrainerEvaluationUseCase.py` (dead code), unregister khỏi `MeetingModuleProvider`, xóa DTO `TrainerSubmitEvaluationRequest`, và dọn dẹp các import thừa trong `evaluation_controller.py`.
- **FR-013**: Frontend MUST tinh giản Tab Báo cáo Đánh giá (`MeetingEvaluationSummaryView.tsx`, `EvaluationOverviewCards.tsx`, `EvaluationCriteriaBreakdownCards.tsx`) bằng cách ẩn khối "Trainer đánh giá Trainee" khi không có dữ liệu (trainerCount === 0).

---

### Key Entities

- **Meeting**: Quản lý thông tin buổi học, hạn chót đánh giá và danh sách thành viên.
- **MeetingParticipant**: Thành viên tham gia buổi học (Trainer hoặc Trainee) và trạng thái điểm danh.
- **MeetingEvaluation**: Phiếu đánh giá của Trainee dành cho Trainer (`TRAINEE_TO_TRAINER`).
- **MeetingOverallEvaluation**: Phiếu đánh giá chất lượng chung của toàn bộ buổi học do Trainer lập.

---

## 🎯 Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Giảm độ phức tạp của giao diện buổi học: Xóa bỏ 1 modal thừa (`TrainerEvaluationModal`) và toàn bộ logic mapping đánh giá cá nhân của Trainer cho từng học viên.
- **SC-002**: 100% các trường hợp tự đánh giá chính mình đều bị chặn với mã lỗi 400 rõ ràng.
- **SC-003**: 0 lỗi vi phạm Hiến pháp Điều XIV (No Fake Optionals) và 0 method dead code trong domain `MeetingParticipant`.
- **SC-004**: 100% Frontend TypeScript check (`npx tsc --noEmit`) và Backend tests (`pytest`) đều pass hoàn toàn.
