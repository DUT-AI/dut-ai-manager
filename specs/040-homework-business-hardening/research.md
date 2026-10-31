# Technical Research & Architecture Decisions: Homework Business Hardening

**Feature**: `040-homework-business-hardening`  
**Date**: 2026-10-31  
**Status**: Completed  

---

## 1. Nghiên cứu & Quyết định 1: Đánh giá trọn vẹn tiến độ bài tập trong Reminder Scanner

### Bối cảnh & Vấn đề
- `HomeworkTaskScanner` hiện đang kiểm tra:
  ```python
  submissions = self.homework_submission_repo.get_submissions_by_user(
      homework_id=hw.id, user_id=uid
  )
  if submissions:
      continue  # Đã nộp bài, bỏ qua
  ```
- **Lỗi nghiệp vụ**:
  - Khi bài tập yêu cầu cả Coding và Game: Nếu học sinh mới nộp Game hoặc mới nộp 1 bài Coding con, mảng `submissions` có 1 phần tử. Scanner lập tức bỏ qua và không gửi thông báo nhắc nhở làm phần còn lại.
  - Khi bài tập có nhiều bài Coding con: Học sinh mới nộp 1 bài hoặc nộp bị Failed (`is_passed == False`), scanner cũng bỏ qua.

### Quyết định Kỹ thuật (Decision 1)
- Sử dụng phương thức Aggregate Root chuẩn của Domain:
  ```python
  evaluation = hw.evaluate_submissions(submissions, deadline=hw_deadline_dt)
  if evaluation.is_submitted:
      continue  # Thực sự hoàn thành tất cả yêu cầu (pass) trước deadline -> Bỏ qua
  ```
- Khi `evaluation.is_submitted == False`, bài tập sẽ được đưa vào danh sách ứng viên nhắc nhở (`ScannedCandidateTask`).
- **Ưu điểm**:
  - Tái sử dụng 100% Domain Logic từ Entity `Homework` (`evaluate_submissions`).
  - Đảm bảo tính nhất quán giữa màn hình hiển thị, kiểm tra vi phạm và hệ thống nhắc nhở.

---

## 2. Nghiên cứu & Quyết định 2: Lấy danh mục bài tập con chính thống từ Quiz API

### Bối cảnh & Vấn đề
- `CheckOverdueHomeworkUseCase` và `GetHomeworkSubmissionStatusUseCase` hiện tự suy diễn danh sách bài con từ các bản ghi `homework_submissions` đã có trong database.
- **Lỗi nghiệp vụ**:
  - Khi bài mới giao chưa có ai nộp: Danh mục bài con bị rỗng (`[]`). Bảng báo cáo hiển thị 0 bài.
  - Khi lớp mới có 1 người nộp bài con A: Hệ thống coi bài tập chỉ có mỗi bài A. Các học sinh khác chỉ cần nộp bài A là hệ thống tưởng đã hoàn thành trọn vẹn cả bài.

### Quyết định Kỹ thuật (Decision 2)
- Tích hợp `QuizApiClient.get_lesson_exercises(slug)` vào:
  1. `GetHomeworkSubmissionStatusUseCase`: Gọi API Quiz để lấy danh mục bài tập con chính thức (`id`, `title`). Dùng danh mục này để dựng bảng báo cáo (`coding_exercises`). Nếu chưa có ai nộp bài, danh mục vẫn hiển thị đầy đủ các bài con từ Quiz.
  2. `CheckOverdueHomeworkUseCase`: Inject `quiz_api: QuizApiClient`. Gọi `await self.quiz_api.get_lesson_exercises(slug)` để xác định tập hợp `required_exercise_ids`.
- **Cơ chế Fallback High-Availability (Resilience)**:
  - Nếu Quiz API trả về lỗi mạng, timeout hoặc `None`, hệ thống tự động fallback dùng danh sách các `exercise_id` đã từng được ghi nhận trong `homework_submissions`.
  - Log warning rõ ràng để phục vụ giám sát và không làm crash tiến trình nền.

---

## 3. Nghiên cứu & Quyết định 3: Rào chắn nghiệp vụ & Hỗ trợ hoãn tích luỹ cho `PostponeStrategy`

### Bối cảnh & Vấn đề
- Hiện tại `PostponeStrategy.validate()` chỉ kiểm tra sơ sài:
  - Không chặn trường hợp `extended_deadline <= now_utc` (xin hoãn lùi về quá khứ).
  - Không chặn trường hợp `current_deadline <= now_utc` (bài tập đã quá hạn nộp nhưng vẫn gửi đơn xin hoãn).
  - Không chặn trường hợp học sinh đã hoàn thành đầy đủ bài tập nhưng vẫn tạo đơn xin hoãn.
- Người dùng chỉ thị rõ ràng: **Cho phép xin hoãn nhiều lần tích lũy**, vì hệ thống vi phạm đã có cơ chế tự động đếm số lần hoãn trong tháng để phạt vi phạm nếu lạm dụng.

### Quyết định Kỹ thuật (Decision 3)
- Bổ sung `homework_submission_repo: HomeworkSubmissionRepository` vào `PostponeStrategy`.
- Bổ sung 3 lớp kiểm tra nghiêm ngặt trong `validate()`:
  1. **Chặn thời gian quá khứ**:
     ```python
     if extended_deadline <= now_utc:
         raise HTTPException(status_code=400, detail="Thời gian gia hạn mới phải ở tương lai")
     ```
  2. **Chặn bài tập đã quá hạn**:
     ```python
     if ensure_utc(current_deadline) <= now_utc:
         raise HTTPException(status_code=400, detail="Bài tập đã quá hạn, không thể tạo đơn xin hoãn")
     ```
  3. **Chặn bài tập đã hoàn thành**:
     ```python
     submissions = self.homework_submission_repo.get_submissions_by_user(homework_id, uid)
     if homework.evaluate_submissions(submissions, deadline=current_deadline).is_submitted:
         raise HTTPException(status_code=400, detail="Bạn đã hoàn thành bài tập này, không thể xin hoãn")
     ```
  4. **Quy tắc hoãn tích lũy (Cumulative Postponement)**:
     - Cho phép học sinh tiếp tục xin hoãn các lần tiếp theo (lần 2, 3...) miễn là tại thời điểm gửi đơn, bài tập chưa hết hạn và khoảng cách thời gian gia hạn mới so với deadline hiện tại thỏa mãn:
       `0 < (extended_deadline - ensure_utc(current_deadline)).total_seconds() <= 4 * 86400`.
     - Không đặt chặn giới hạn số lần cho riêng 1 bài tập vì hệ thống kỷ luật toàn cục sẽ tự động bắt lỗi khi số lần hoãn trong tháng vượt ngưỡng.
