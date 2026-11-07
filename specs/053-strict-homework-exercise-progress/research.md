# Research & Architectural Analysis: Chuẩn hóa nghiêm ngặt tiến độ bài tập con và tách biệt Game Quiz

**Feature**: `053-strict-homework-exercise-progress`  
**Date**: 2026-11-08  
**Status**: Completed

---

## 1. Nghiên cứu nguyên nhân gốc rễ (Root Cause Analysis)

### 1.1. Lỗi thiếu bài tập con phía Học viên (`MyHomeworkDetailPage`)
* **Thực trạng**: Màn hình học viên gọi API `GET /homeworks/{id}` (`GetHomeworkDetailUseCase`).
* **Vấn đề**:
  - DTO `HomeworkResponseDetail` chỉ trả về: `id`, `title`, `deadline`, `requires_coding`, `requires_game`, `link`, `slug`, `assignee_ids`. **Hoàn toàn không có danh mục bài tập con `coding_exercises`**.
  - Frontend gọi tiếp `useMyHomeworkSubmissions` (`GET /homeworks/{id}/my-submissions`), chỉ nhận về mảng bài mà học viên này đã nộp.
  - Khi render tab Coding, component `UnifiedSubmissionTimeline` không nhận được prop `allExercises`.
  - Hàm `groupSubmissionsByExercise` khi không có `allExercises` sẽ tự gom nhóm dựa trên mảng `submissions` đã nộp.
  - Nếu học viên chưa nộp bài con nào, bài con đó không có trong `submissions` ➔ bị biến mất khỏi giao diện. Học viên mới nộp 1/2 bài thì frontend tự tính tổng số bài là 1 và kết luận "Hoàn thành 1/1 (100%)".

### 1.2. Lỗi fallback "Bài tập chung" phía Admin Modal (`SubmissionHistoryModal`)
* **Thực trạng**: Admin gọi API `GET /homeworks/{id}/submission-status`, nhận được `coding_exercises` đầy đủ 2 bài.
* **Vấn đề**:
  - `SubmissionHistoryModal` nhận `submissions` từ API `GET /homeworks/{id}/users/{userId}/submissions` (gồm cả bản ghi CODING và GAME).
  - Modal truyền toàn bộ `submissions` (chứa cả GAME) vào `UnifiedSubmissionTimeline` với `type="CODING"`.
  - Bản ghi Game Quiz không có `exercise_id`.
  - Hàm `groupSubmissionsByExercise` ở bước 2 lặp qua các bản ghi chưa khớp với `allExercises`: nó bắt gặp bản ghi GAME và tự động gán key `__general__` với tiêu đề `"Bài tập chung"`.
  - Kết quả: Bài tập Coding bị đội thêm 1 bài con ảo (thành 3 bài: 2 coding + 1 game quiz), hiển thị `Tiến độ (2/3) - 67%`, mâu thuẫn trực tiếp với tiêu đề modal `1/2 bài con`.

### 1.3. Lỗi hiển thị và hardcode chữ "100%" của Game Quiz
* **Thực trạng**:
  - Trong `SubmissionItemCard.tsx`:
    + Điểm số: `{submission.score} / 10`. Điểm Game Quiz lưu `89.0` (thang 100 hoặc điểm tích lũy Quiz) ➔ hiển thị thành `89 / 10`.
    + Số câu đúng: `{submission.correctCount} / {submission.totalQuestions} câu (100%)` ➔ hardcode cứng chữ `(100%)`.
  - Trong `MyHomeworkDetailPage.tsx`:
    + Banner: gõ cứng `"đúng 100%"`.
    + Tab: `isGameSubmitted = gameSubmissions.length > 0` ➔ gắn nhãn `Đã xong 100%`.
* **Nghiệp vụ thực tế**:
  - Quiz API và Backend định nghĩa: Học viên hoàn thành phiên chơi game (`is_completed: true` trên Quiz) là đạt `is_passed = True`.
  - Không có quy tắc nào bắt buộc phải trả lời đúng 100% số câu hỏi mới được tính là hoàn thành.

---

## 2. Giải pháp kỹ thuật và Thiết kế kiến trúc

### 2.1. Backend Design (Clean Architecture & Constitution Principle I, V)
1. **Mở rộng DTO `HomeworkResponseDetail`**:
   - Thêm trường `coding_exercises: list[ExerciseSummaryDTO] = Field(default_factory=list)`.
   - Giữ nguyên tính tương thích ngược (Backward Compatibility - Principle V).
2. **Cập nhật `GetHomeworkDetailUseCase`**:
   - Inject thêm `QuizApiClient` và `HomeworkSubmissionRepository`.
   - Khi load chi tiết bài tập:
     - Lấy danh mục bài tập coding con từ Quiz API qua `homework.slug`.
     - Nếu Quiz API không khả dụng, trích xuất từ các bài nộp đã lưu trong `homework_submissions`.
     - Trả về `HomeworkResponseDetail` kèm danh mục `coding_exercises`.

### 2.2. Frontend Design (Single Source of Truth & Strict Grouping)
1. **Cập nhật Types (`homework.types.ts`)**:
   - Mở rộng `homeworkSchema` với trường `coding_exercises: z.array(exerciseSummarySchema).optional()`.
2. **Loại bỏ Fallback trong `submissionUtils.ts`**:
   - Hàm `groupSubmissionsByExercise(submissions, allExercises)`:
     - **Bước 1**: Lọc nghiêm ngặt: chỉ duyệt các submission có `s.submissionType === 'CODING'`. Bỏ qua hoàn toàn `GAME`.
     - **Bước 2**: Nếu có `allExercises`, duyệt qua danh mục bài con chính thức. Với mỗi bài, tìm bài nộp tương ứng của học viên. Nếu chưa nộp, tạo summary với `attemptCount: 0, isPassed: false`.
     - **Bước 3**: Tuyệt đối **KHÔNG tạo nhóm fallback `__general__` mang tên "Bài tập chung"** cho timeline bài tập Coding.
3. **Cập nhật `MyHomeworkDetailPage.tsx`**:
   - Truyền `allExercises={homework.coding_exercises}` vào `UnifiedSubmissionTimeline` của tab Coding.
   - Sửa banner thông báo: thay `"đúng 100%"` bằng `"Hoàn thành Game trắc nghiệm"`.
   - Kiểm tra trạng thái Game: `isGamePassed = gameSubmissions.some(s => s.isPassed)` ➔ Hiển thị thẻ `"Đã hoàn thành"` thay vì `"Đã xong 100%"`.
4. **Cập nhật `SubmissionHistoryModal.tsx` (Admin Modal)**:
   - Tách thành 2 Tabs (hoặc 2 sections rõ ràng): **Bài tập Coding** và **Trắc nghiệm Game Quiz**, tương tự cấu trúc trang học viên.
   - Chỉ truyền `codingSubmissions` và `allExercises` vào timeline Coding.
   - Truyền `gameSubmissions` vào timeline Game với `showExerciseOverview={false}`.
   - Đồng bộ hoàn toàn số liệu giữa tiêu đề modal và thân modal (đều là `1/2 bài con`).
5. **Cập nhật `SubmissionItemCard.tsx`**:
   - Hiển thị điểm:
     - Nếu `CODING`: `{submission.score} / 10`.
     - Nếu `GAME`: `{submission.score} điểm` (không kèm `/ 10`).
   - Hiển thị số câu đúng:
     - Tính tỷ lệ phần trăm thực tế:
       ```tsx
       const percent = submission.totalQuestions && submission.totalQuestions > 0
         ? Math.round((submission.correctCount / submission.totalQuestions) * 100)
         : null;
       ```
     - Hiển thị: `{submission.correctCount} / {submission.totalQuestions} câu {percent !== null ? `(${percent}%)` : ''}`.
     - Xóa bỏ chuỗi cứng `(100%)`.

---

## 3. Đánh giá rủi ro và Kế hoạch xác minh

| Rủi ro | Mức độ | Biện pháp giảm thiểu |
| :--- | :---: | :--- |
| Bài tập không có `slug` hoặc Quiz API offline | Thấp | Use case fallback lấy danh mục bài tập con đã lưu từ các bài nộp của lớp trong DB. |
| Học sinh chưa có bài nộp nào cho bài học | Trung bình | Giao diện vẫn nhận được `coding_exercises` từ bài học, hiển thị 0/N bài hoàn thành và danh sách các bài cần làm. |
| Backward compatibility với API client cũ | Thấp | DTO `HomeworkResponseDetail` chỉ thêm trường tùy chọn (default empty list), không thay đổi kiểu dữ liệu các trường hiện có. |
