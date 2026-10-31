# Phase 0: Research & Technical Decisions (038-violation-delay)

## Vấn đề cần giải quyết & Làm rõ

1. **Khẳng định nguyên tắc phạt vi phạm**:
   - Khi job quét chạy vào ngày $T+2$, hệ thống **TUYỆT ĐỐI KHÔNG GIA HẠN** cho các task hoàn thành sau deadline.
   - Bất kỳ task nào nộp/hoàn thành trễ so với deadline ban đầu hoặc chưa hoàn thành **ĐỀU BỊ TẠO VI PHẠM**.
2. **Kỹ thuật kiểm tra bài tập quá hạn (`CheckOverdueHomeworkUseCase`)**:
   - Khi bài tập có deadline là ngày $T$, và job quét chạy vào ngày $T+2$:
   - Trong cơ sở dữ liệu: `HomeworkSubmissionModel.submitted_at <= homework.deadline` (bài nộp sau deadline bị loại bỏ khỏi điều kiện hợp lệ).
   - **Tối ưu hóa kiến trúc**: Loại bỏ việc gọi trực tiếp Quiz API trong `CheckOverdueHomeworkUseCase`. Việc kiểm tra chỉ dựa trên danh sách phân công (`assignees`) và bài nộp trong Database (`submissions`). Dữ liệu bài nộp được đẩy qua Webhook hoặc job đồng bộ (`SyncHomeworkFromQuizUseCase`). Cách này loại bỏ phụ thuộc mạng bên ngoài, tăng tốc độ quét và loại bỏ rủi ro rớt API từ bên thứ ba.
3. **Vị trí tính toán độ trễ 2 ngày**:
   - Tính ở cấp Use Case (khi `target_date is None`), giữ nguyên ngày khi truyền tham số cụ thể.
4. **Hạn kiểm tra đánh giá cuộc họp (`CheckEvaluationDeadlineJobUseCase`)**:
   - `MEETING_EVALUATION_DEADLINE_HOURS = 72` (quét các buổi học kết thúc quá 72h).
   - `MEETING_EVALUATION_SCAN_WINDOW_DAYS = 9`.

---

## Các Quyết định Kỹ thuật (Decisions & Rationale)

### 1. Phạt nghiêm ngặt các trường hợp trễ deadline
- **Quyết định**: Mốc deadline ban đầu của task là ranh giới duy nhất để đánh giá hợp lệ.
  - Bài nộp có `submitted_at <= homework.deadline` -> Hợp lệ.
  - Bài nộp có `submitted_at > homework.deadline` -> Trễ deadline -> Bị tạo vi phạm.
  - Không nộp bài -> Chưa hoàn thành -> Bị tạo vi phạm.
- **Lý do**: Đúng với yêu cầu của ban quản trị: Độ trễ 2 ngày chỉ là độ trễ thời điểm quét của hệ thống nhằm phục vụ việc kiểm tra, đối soát và ổn định dữ liệu, không phải chính sách nới lỏng deadline cho học viên.

### 2. Vị trí tính toán độ trễ & xử lý `target_date`
- **Quyết định**: Đặt logic mặc định tại **Use Case level**:
  ```python
  if target_date is None:
      now = datetime.now(UTC)
      today_vn = now.astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).date()
      target_date = today_vn - timedelta(days=VIOLATION_CHECK_DELAY_DAYS)
  ```
- **Lý do**: Giữ nguyên tính độc lập của Use Case và cho phép test script / admin trigger ngày cụ thể mà không bị trừ lùi lần thứ hai.

### 3. Cập nhật Đánh giá cuộc họp (`CheckEvaluationDeadlineJobUseCase`)
- **Quyết định**:
  - `MEETING_EVALUATION_DEADLINE_HOURS = 72`
  - `MEETING_EVALUATION_SCAN_WINDOW_DAYS = 9`
  - Lý do vi phạm:
    - `"Chưa hoàn thành đánh giá Trainer cho buổi học '{meeting.title}'{time_str} trong vòng 72h"`
    - `"Trainer chưa hoàn tất đánh giá tổng thể buổi học '{meeting.title}'{time_str} trong vòng 72h"`

---

## Tóm tắt Rà soát
- [x] Làm rõ nguyên tắc không gia hạn nộp bài. Task nộp trễ deadline vẫn bị tạo vi phạm.
- [x] Độ trễ 2 ngày là độ trễ chạy job quét của hệ thống.
- [x] Áp dụng nhất quán cho 4 jobs.
