# Nghiên cứu Kỹ thuật: Tinh giản Đánh giá Meeting & Chuẩn hóa Kiến trúc Full Stack

**Feature Branch**: `046-harden-meeting-evaluation`  
**Ngày thực hiện**: 2026-11-04  
**Trạng thái**: Hoàn thành (Resolved all unknowns)

---

## 1. Loại bỏ Đánh giá cá nhân Trainer-to-Trainee (`TRAINER_TO_TRAINEE`)

### Bối cảnh & Vấn đề
Mô hình đánh giá buổi học ban đầu được thiết kế theo dạng 2 chiều đối xứng:
- Trainee đánh giá Trainer (`TRAINEE_TO_TRAINER`).
- Trainer chấm điểm từng Trainee riêng lẻ (`TRAINER_TO_TRAINEE`).

Tuy nhiên, trong môi trường đào tạo thực tế tại DUT:
1. Mỗi buổi học có thể có từ 20 đến 100 học viên. Việc yêu cầu Trainer phải mở từng modal để chấm điểm 4 tiêu chí cho từng học viên tạo ra gánh nặng thao tác cực lớn và không khả thi.
2. Việc Trainer chấm điểm cá nhân dẫn đến việc sinh ra `GetMyEvaluationResultUseCase` với giả định sai lệch rằng `meeting.created_by` luôn là Trainer, gây lỗi nếu người tạo meeting là Admin/Leader.
3. Trainer đã có tính năng **Đánh giá tổng thể toàn bộ buổi học** (`MeetingOverallEvaluation`) với 4 tiêu chí chuẩn đại diện cho cả lớp học:
   - Mức độ chuẩn bị & tham gia lớp học
   - Khả năng tiếp thu & hiểu bài
   - Mức độ tương tác & tinh thần đóng góp
   - Kỷ luật lớp học & chấp hành nội quy

### Quyết định (Decision)
- **Bỏ hoàn toàn luồng đánh giá cá nhân Trainer chấm từng Trainee**.
- Trainer chỉ thực hiện **Đánh giá tổng thể toàn bộ lớp học** (`MeetingOverallEvaluation`).
- Trainee thực hiện **Đánh giá Trainer** phụ trách buổi học (`TRAINEE_TO_TRAINER`).
- **Backend**:
  - Deprecate/vô hiệu hóa `SubmitTrainerEvaluationUseCase` và endpoint `POST /{meeting_id}/evaluations/trainer` (trả về lỗi `400 Bad Request` giải thích rõ chức năng này đã được thay thế bằng Đánh giá tổng thể).
  - Tinh giản `GetMyEvaluationResultUseCase` hoặc trả về kết quả an toàn không gây lỗi.
- **Frontend**:
  - Xóa bỏ file `frontend/src/features/meeting/components/TrainerEvaluationModal.tsx`.
  - Dọn dẹp export `TrainerEvaluationModal` khỏi `frontend/src/features/meeting/components/index.ts`.
  - Xóa bỏ nút bấm "Chấm điểm" / "Đã ĐG" trong `ParticipantActionButtons.tsx`.
  - Xóa bỏ `trainerEvalsByTraineeId` và logic lọc theo trạng thái chấm điểm cá nhân trong `TraineeListTable.tsx` và `MeetingParticipantsTab.tsx`.

### Lý do lựa chọn (Rationale)
- Tinh giản tối đa trải nghiệm người dùng: Trainer chỉ cần đánh giá đúng 1 lần cho cả lớp.
- Tuân thủ Điều X của Hiến pháp (Zero Redundant Backward Compatibility): Loại bỏ dứt điểm mã nguồn thừa và các điểm nghẽn logic thay vì duy trì các lớp bọc tạm bợ.

### Phương án thay thế bị từ chối (Alternatives Rejected)
- **Giữ cả 2 luồng song song**: Bị từ chối vì làm tăng độ phức tạp của code, giao diện rối rắm và vi phạm yêu cầu rõ ràng từ người dùng.

---

## 2. Siết chặt Domain Invariants & Chống Tự Đánh giá

### Bối cảnh & Vấn đề
Trong `SubmitTraineeEvaluationUseCase`:
- Người dùng có thể vô tình hoặc cố ý tự đánh giá chính mình nếu họ vừa là Trainer vừa là Trainee, hoặc gọi API trực tiếp với `target_user_id == reviewer_id`.
- Chưa có invariant kiểm tra nghiêm ngặt `target_user_id` bắt buộc phải nằm trong danh sách `meeting.trainers`.
- Trong `SubmitMeetingOverallEvaluationUseCase`, chưa kiểm tra xem người gửi đánh giá có phải là Trainer của buổi học hoặc Admin/Creator hay không.

### Quyết định (Decision)
1. **Trong `SubmitTraineeEvaluationUseCase`**:
   - Xác thực: `if reviewer_id == resolved_target_id: raise BadRequestException("Không thể tự đánh giá chính mình")`.
   - Xác thực: `if not meeting.is_trainer(resolved_target_id): raise BadRequestException("Người được đánh giá không phải là Trainer của buổi học này")`.
2. **Trong `SubmitMeetingOverallEvaluationUseCase`**:
   - Xác thực: `if not is_admin and not meeting.is_trainer(trainer_id) and meeting.created_by != trainer_id: raise BadRequestException("Chỉ Giảng viên phụ trách hoặc Người tạo buổi học mới có quyền gửi đánh giá tổng thể", status_code=403)`.

### Lý do lựa chọn (Rationale)
- Đảm bảo tính toàn vẹn dữ liệu (Data Integrity) và quy tắc nghiệp vụ bất biến (Domain Invariants) theo Clean Architecture.

---

## 3. Tuân thủ Hiến pháp Điều XIV (No Fake Optionals)

### Bối cảnh & Vấn đề
Trong `GetMeetingEvaluationSummaryUseCase.__init__`:
```python
def __init__(
    self,
    meeting_repo: MeetingRepository,
    evaluation_repo: MeetingEvaluationRepository,
    overall_eval_repo: MeetingOverallEvaluationRepository | None = None,
):
    self.meeting_repo = meeting_repo
    self.evaluation_repo = evaluation_repo
    self.overall_eval_repo = overall_eval_repo
```
Và trong `execute()`:
```python
if self.overall_eval_repo:
    overall_entity = self.overall_eval_repo.get_by_meeting_id(meeting_id)
```
Điều này vi phạm nghiêm trọng **Điều XIV của Hiến pháp** (Cấm Fake Optionals & Cấm code phòng thủ giả tạo). Trên thực tế, Dishka Provider đã cấu hình tiêm `overall_eval_repo` 100%.

### Quyết định (Decision)
- Sửa tham số constructor:
  ```python
  def __init__(
      self,
      meeting_repo: MeetingRepository,
      evaluation_repo: MeetingEvaluationRepository,
      overall_eval_repo: MeetingOverallEvaluationRepository,
  ):
      self.meeting_repo = meeting_repo
      self.evaluation_repo = evaluation_repo
      self.overall_eval_repo = overall_eval_repo
  ```
- Xóa bỏ câu lệnh `if self.overall_eval_repo:` trong `execute()`. Gọi trực tiếp `self.overall_eval_repo.get_by_meeting_id(meeting_id)`.
- Cập nhật toàn bộ các bài test khởi tạo use case này trong `tests/unit/test_meeting_evaluation.py`.

### Lý do lựa chọn (Rationale)
- Tuân thủ nguyên tắc Fail-Fast: Phát hiện lỗi dependency injection ngay tại compile-time / startup thay vì âm thầm bỏ qua dữ liệu ở runtime.

---

## 4. Tối ưu hóa Database Query (Loại bỏ Truy vấn Lặp)

### Bối cảnh & Vấn đề
Khi gọi `POST /{meeting_id}/evaluations/overall`:
1. Dependency `check_meeting_evaluation_permission` gọi `uc.get_by_id(meeting_id)`, thực hiện query cơ sở dữ liệu kèm `selectinload(participants)` và `joinedload(creator)`.
2. Sau khi dependency vượt qua, Use Case `SubmitMeetingOverallEvaluationUseCase.execute` lại gọi `self.meeting_repo.get_by_id(meeting_id)` một lần nữa.
Điều này làm tăng gấp đôi số lượng truy vấn SQL không cần thiết trong cùng một request.

### Quyết định (Decision)
- Chuyển toàn bộ quyền kiểm tra (Authorization Check) vào trong `SubmitMeetingOverallEvaluationUseCase.execute`. Use Case nhận cờ `is_admin: bool` từ `current_user` trong Controller.
- Bỏ dependency `Depends(check_meeting_evaluation_permission)` ở route `submit_meeting_overall_evaluation`.
- Endpoint `submit_meeting_overall_evaluation` chỉ thực hiện đúng 1 truy vấn `meeting_repo.get_by_id(meeting_id)`.

### Lý do lựa chọn (Rationale)
- Tiết kiệm 50% tài nguyên truy vấn cơ sở dữ liệu cho các request đánh giá.
- Tăng tính gắn kết (Cohesion): Use case quản lý trọn vẹn nghiệp vụ và thẩm quyền đối với thực thể `Meeting`.

---

## 5. Hiển thị Hạn chót Đánh giá trên Frontend

### Bối cảnh & Vấn đề
`MeetingHeroHeader` hiện tại chỉ hiển thị một tag thông tin cố định `"Đánh giá 2 chiều (Hạn 24h)"`. Học viên không nắm được mốc thời gian cụ thể khi nào cổng đánh giá sẽ đóng.

### Quyết định (Decision)
- Trên `MeetingHeroHeader`:
  - Đọc trường `meeting.evaluation_deadline`.
  - Nếu `meeting.enable_evaluation` bật:
    - Nếu có `evaluation_deadline`: Hiển thị Tag rõ ràng kèm icon đồng hồ `Hạn chót: DD/MM/YYYY HH:mm` (Asia/Ho_Chi_Minh).
    - Nếu đã qua hạn chót: Đổi trạng thái sang màu cảnh báo `Đã hết hạn đánh giá`.
    - Nếu chưa có deadline cụ thể: Hiển thị `Đang mở đánh giá`.

### Lý do lựa chọn (Rationale)
- Cung cấp thông tin minh bạch, rõ ràng cho học viên, nâng cao trải nghiệm người dùng (UX).
