# Phase 0 Research: Thống nhất Trạng thái Hoàn thành Bài tập giữa Học viên và Quản lý

**Feature**: `069-unify-homework-submission-status`  
**Date**: 2026-11-15  

## Nghiên cứu 1: Cơ chế Xác định Danh mục Bài tập Coding con (Required Coding Exercises)

### Vấn đề (Context)
* Tại `GetUserHomeworksUseCase` (danh sách bài tập học viên phân trang 20 bài) và `GetUnsubmittedHomeworksForUserUseCase`, nếu mỗi bài tập đều gọi HTTP sang Quiz API (`get_lesson_exercises(slug)`), mỗi lượt tải trang sẽ phát sinh tới 20 network requests đồng thời. Điều này gây suy giảm nghiêm trọng độ trễ (latency > 1-2s) và phụ thuộc lớn vào sự sẵn sàng của Quiz API bên ngoài.
* Ngược lại, trong cơ sở dữ liệu bảng `homework_submissions`, các bài nộp coding của học sinh đã lưu trữ `exercise_id` và `exercise_title`. Ngoài ra khi Admin thực hiện đồng bộ (Sync Quiz), các bài nộp cũng đã được kéo về đầy đủ.

### Quyết định (Decision)
* **Giải pháp kết hợp (Hybrid DB-First với Repository Aggregation)**:
  1. Bổ sung phương thức truy vấn tối ưu trong `HomeworkSubmissionRepository`: `get_required_exercise_ids_map(homework_ids: list[int]) -> dict[int, set[str]]`. Phương thức này thực thi một câu lệnh SQL duy nhất:
     ```sql
     SELECT homework_id, exercise_id 
     FROM homework_submissions 
     WHERE homework_id IN (:hw_ids) 
       AND UPPER(submission_type) = 'CODING' 
       AND exercise_id IS NOT NULL 
       AND exercise_id NOT LIKE 'sync-legacy%'
     GROUP BY homework_id, exercise_id
     ```
  2. Bổ sung Domain Service / Helper `HomeworkExerciseResolver` đóng vai trò phân giải tập `required_exercise_ids`:
     - Ưu tiên lấy từ cơ sở dữ liệu `homework_submissions` đã có.
     - Với các use case đơn lẻ theo ID (như `GetHomeworkDetailUseCase`, `GetHomeworkSubmissionStatusUseCase`), tiếp tục hỗ trợ truy vấn trực tiếp từ Quiz API khi có `slug`.
* **Ưu điểm**:
  - Không tạo thêm HTTP request nào khi học viên mở trang danh sách bài tập.
  - Tốc độ xử lý tại Database < 2ms cho tập 20 bài tập.
  - Tuân thủ nguyên tắc Constitution Principle I và IX (Domain Services thuần túy, không kế thừa Base Use Case).

---

## Nghiên cứu 2: Chuẩn hóa Domain Logic trên Aggregate Root `Homework`

### Vấn đề (Context)
* Hiện tại `Homework.evaluate_submissions` trong `backend/app/homework/domain/entity.py` đang dùng:
  ```python
  coding_submitted = any(s.submission_type == "CODING" and s.is_passed for s in submissions)
  ```
  Hàm này hoàn toàn không biết bài tập có bao nhiêu bài coding con, dẫn đến chỉ cần pass 1 bài là gán cờ `is_submitted = True`.

### Quyết định (Decision)
* Mở rộng tham số hàm `evaluate_submissions`:
  ```python
  def evaluate_submissions(
      self,
      submissions: list["HomeworkSubmission"],
      deadline: datetime | None = None,
      reference_time: datetime | None = None,
      required_exercise_ids: set[str] | None = None,
  ) -> SubmissionEvaluation:
  ```
* **Quy tắc đánh giá Coding**:
  - Nếu `required_exercise_ids` có dữ liệu ($N > 0$):
    - `passed_ex_ids = {str(s.exercise_id) for s in submissions if str(s.submission_type).upper() == "CODING" and s.is_passed and s.exercise_id}`
    - `completed_coding_count = len(passed_ex_ids & required_exercise_ids)`
    - `total_coding_required = len(required_exercise_ids)`
    - `coding_submitted = required_exercise_ids.issubset(passed_ex_ids)`
    - `coding_status = self.determine_coding_status(completed_coding_count, total_coding_required)`
  - Nếu `required_exercise_ids` không có hoặc rỗng:
    - Fallback kiểm tra xem có bất kỳ bài coding nào pass không (tương thích cho bài cũ).
* **Quy tắc đánh giá Tổng thể (`is_submitted`)**:
  - `is_submitted = (not has_coding or coding_submitted) and (not has_game or game_submitted)`
  - Nếu `has_coding and not coding_submitted`:
    - Nếu $total\_required > 1$ và $completed > 0$: thêm `"Còn {thiếu}/{tổng} bài tập Coding"` vào `uncompleted_items`.
    - Nếu chưa làm bài nào: thêm `"Bài tập Coding"` vào `uncompleted_items`.
* **Cập nhật Value Object `SubmissionEvaluation`**:
  - `coding_status: str` ("COMPLETED" | "PARTIALLY_SUBMITTED" | "NOT_SUBMITTED")
  - `total_coding_required: int`
  - `total_coding_completed: int`
* **Cập nhật DTO `HomeworkResponse`**:
  - Bổ sung 3 trường trên vào DTO trả về cho client.

---

## Nghiên cứu 3: Đồng bộ UX/UI trên Frontend (`HomeworkCard` & `MyHomeworkPage`)

### Vấn đề (Context)
* `HomeworkCard` hiện chỉ hiển thị 2 trạng thái chính: "Đã nộp" (xanh lá) hoặc "Chưa nộp" (trung tính/đỏ nếu quá hạn).
* Nó chỉ kiểm tra `isPartial` khi `hasBoth && !isSubmitted && !!(coding_submitted || game_submitted)`, hoàn toàn bỏ qua trường hợp bài tập coding có nhiều bài con.

### Quyết định (Decision)
* Cập nhật điều kiện xác định trạng thái trong `HomeworkCard`:
  - `isFullySubmitted = homework.is_submitted === true`
  - `isPartial = !isFullySubmitted && (homework.coding_status === 'PARTIALLY_SUBMITTED' || (homework.has_coding && homework.has_game && !!(homework.coding_submitted || homework.game_submitted)))`
* Khi `isPartial`:
  - Accent viền trái: Dải màu hổ phách/cam (`from-amber-400 to-orange-500`).
  - Icon trạng thái: `ClockCircleOutlined` hoặc `ExclamationCircleOutlined` màu cam.
  - Tag hiển thị:
    - Nếu có thông tin bài con ($N > 1$): `Tag color="warning"` với nội dung: `Tiến độ: {total_coding_completed}/{total_coding_required} bài con`.
    - Kèm theo cảnh báo các phần chưa hoàn thành trong `uncompleted_items`.
* Tại `MyHomeworkPage`:
  - Tab "Chưa nộp" (`unsubmitted`): Lọc theo `!hw.isSubmitted` (bao gồm cả các bài làm dở `isPartial`).
  - Tab "Đã nộp" (`submitted`): Chỉ lọc các bài `hw.isSubmitted === true`.
  - Thống kê tổng số lượng bài đã nộp / chưa nộp phản ánh đúng tiêu chí này.

---

## Nghiên cứu 4: Đảm bảo Tương thích Báo cáo & Trình quét Nhắc nhở (Scanners)

### Vấn đề (Context)
* `GetUnsubmittedHomeworksForUserUseCase`, `GetUnsubmittedHomeworkReportUseCase` và `HomeworkTaskScanner` (hệ thống nhắc deadline bot) đều dựa vào `hw.evaluate_submissions`.
* Nếu bài làm dở bị bỏ sót, học sinh sẽ không nhận được nhắc nhở bot và quản lý sẽ thấy báo cáo số bài chưa nộp bị thiếu.

### Quyết định (Decision)
* Áp dụng `get_required_exercise_ids_map` cho cả `GetUnsubmittedHomeworksForUserUseCase`, `GetUnsubmittedHomeworkReportUseCase` và `HomeworkTaskScanner`.
* Đảm bảo mọi học sinh có bài tập làm dở đều được:
  1. Hiển thị trong báo cáo chưa nộp của Quản lý.
  2. Được quét vào danh sách cần gửi thông báo nhắc nhở trước hạn chót.
