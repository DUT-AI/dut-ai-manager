# Feature Specification: Chuyển hoàn toàn trường Deadline của Homework sang bảng Assignees & Tích hợp đơn xin hoãn (039-per-assignee-homework-deadline)

## Bối cảnh & Mục tiêu
- **Hiện tại**: Trường `deadline` nằm ở bảng `homeworks` (dùng chung cho toàn bộ bài tập). Khi học viên tạo đơn xin hoãn (`POSTPONE`), hệ thống không cập nhật hạn nộp của riêng học viên đó. Dẫn đến việc job quét vi phạm quét theo bài tập gốc bị lọt vi phạm sau khi hết hạn hoãn, và giao diện học viên không hiển thị hạn nộp đã gia hạn.
- **Yêu cầu cốt lõi**:
  - **Xóa bỏ hoàn toàn trường `deadline` khỏi bảng `homeworks`**.
  - **Dời trường `deadline` sang bảng `homework_assignees`**: Mỗi học viên khi được giao bài tập sẽ có một mốc `deadline` riêng (`homework_assignees.deadline`).
  - **Tích hợp Đơn xin hoãn (`POSTPONE`)**: Khi học viên tạo đơn xin hoãn bài tập, hệ thống tự động cập nhật `deadline` của học viên đó trong bảng `homework_assignees`. Trong payload của đơn lưu `old_deadline` để có thể hoàn nguyên khi đơn bị xoá/hủy.
  - **Job quét vi phạm (`CheckOverdueHomeworkUseCase`)**: Quét vi phạm độc lập cho từng học viên dựa theo `homework_assignees.deadline` (mặc định trễ 2 ngày).

---

## User Stories & Acceptance Criteria

### User Story 1: Chuyển đổi Schema - Xóa `deadline` ở Homeworks, đưa sang Homework Assignees (Priority: P1) 🎯 MVP
**Là một** Lập trình viên hệ thống,  
**Tôi muốn** trường `deadline` được chuyển hẳn từ bảng `homeworks` sang bảng `homework_assignees`,  
**Để** dữ liệu hạn nộp phản ánh chính xác từng cá nhân học viên theo Clean Architecture và Constitution Rule X.

- **AC 1.1**: Bảng `homework_assignees` có cột `deadline: DateTime(timezone=True)` (NOT NULL, có index).
- **AC 1.2**: Viết migration script:
  1. Thêm cột `deadline` vào `homework_assignees`.
  2. Backfill dữ liệu `deadline` từ `homeworks` sang `homework_assignees`.
  3. Cập nhật `deadline` trong `homework_assignees` cho các đơn `POSTPONE` đang có hiệu lực.
  4. Xoá bỏ (`DROP COLUMN`) cột `deadline` khỏi bảng `homeworks`.
- **AC 1.3**: Xoá trường `deadline` khỏi `HomeworkModel`, `HomeworkEntity`, `HomeworkCreate`, `HomeworkUpdate` (deadline khi tạo/sửa sẽ được truyền trực tiếp vào danh sách phân công hoặc làm tham số đầu vào gán cho assignees).
- **AC 1.4**: Bổ sung trường `deadline` vào `HomeworkAssigneeModel`, `HomeworkAssignee` Entity.

### User Story 2: Tạo và quản lý Bài tập với Deadline theo Assignee (Priority: P1)
**Là một** Admin / Trainer khi giao bài tập,  
**Tôi muốn** khi tạo hoặc phân công bài tập, hạn nộp được lưu trực tiếp vào từng bản ghi phân công của học viên,  
**Để** mỗi học viên có hạn nộp cụ thể và độc lập.

- **AC 2.1**: Trong `CreateHomeworkUseCase`: Khi Admin tạo bài tập và cung cấp danh sách học viên kèm deadline (hoặc deadline chung cho đợt giao đó), hệ thống lưu các bản ghi `homework_assignees(homework_id, user_id, deadline)`.
- **AC 2.2**: Khi phân công thêm học viên mới qua `UpdateHomeworkUseCase`, bản ghi assignee mới được tạo với deadline tương ứng.
- **AC 2.3**: API danh sách bài tập của Admin (`GetHomeworksUseCase`): Hiển thị hạn nộp tổng quan (ví dụ: `earliest_deadline` hoặc `latest_deadline` từ các assignees của bài tập).

### User Story 3: Tích hợp Đơn xin hoãn nộp bài tập (`POSTPONE`) (Priority: P1)
**Là một** Học viên khi nộp đơn xin hoãn bài tập,  
**Tôi muốn** hạn nộp cá nhân của tôi trong bảng `homework_assignees` được cập nhật sang thời gian gia hạn mới,  
**Để** tôi có thêm thời gian nộp bài hợp lệ mà không bị ghi nhận vi phạm sớm.

- **AC 3.1**: Cập nhật `PostponePayload` bổ sung trường `old_deadline: datetime | None = None` để ghi nhận hạn nộp trước khi xin hoãn.
- **AC 3.2**: Trong `PostponeStrategy.validate()`: Lấy deadline hiện tại của học viên từ `homework_assignee_repo.get_user_deadline(homework_id, user_id)`. Kiểm tra `request.payload.start_time > current_deadline` và khoảng cách gia hạn không vượt quá 4 ngày so với deadline hiện tại.
- **AC 3.3**: Trong `PostponeStrategy.on_created`:
  1. Ghi nhận `payload.old_deadline = current_deadline`.
  2. Cập nhật `homework_assignee_repo.update_deadline(homework_id, user_id, new_deadline=request.payload.start_time)`.
- **AC 3.4**: Trong `PostponeStrategy.on_deleted`: Hoàn nguyên deadline của học viên về `payload.old_deadline`.

### User Story 4: Quét vi phạm bài tập theo Deadline của từng Assignee (Priority: P1)
**Là một** Hệ thống quản trị tự động,  
**Tôi muốn** job kiểm tra vi phạm quét trực tiếp các bản ghi `homework_assignees` có deadline đến hạn,  
**Để** xử lý vi phạm đúng thời điểm sau 2 ngày kể từ deadline cá nhân của từng học viên.

- **AC 4.1**: `CheckOverdueHomeworkUseCase` truy vấn các bản ghi `homework_assignees` có `date(deadline) == target_date` (mặc định `today_vn - 2 days`).
- **AC 4.2**: Với mỗi bản ghi đến hạn: Đối soát bài nộp trong DB của đúng học viên đó (`submitted_at <= assignee.deadline`).
- **AC 4.3**: Nếu học viên chưa hoàn thành trước `assignee.deadline` $\rightarrow$ Phát sự kiện `HomeworkOverdueDetected` để xử lý vi phạm.
- **AC 4.4**: Học viên có đơn hoãn bài tập chỉ bị quét khi deadline gia hạn của họ đến ngày đối soát (không bị quét nhầm vào ngày deadline ban đầu, và không bị lọt sau khi hết hạn hoãn).

### User Story 5: Hiển thị Deadline cá nhân trên giao diện Học viên (Priority: P2)
**Là một** Học viên vào xem "Bài tập của tôi" (`/my-homeworks`),  
**Tôi muốn** thấy hạn nộp bài tập là hạn nộp cá nhân của chính tôi (kể cả khi đã xin hoãn thành công),  
**Để** biết chính xác hạn nộp bài của bản thân.

- **AC 5.1**: `GetMyHomeworksUseCase` và `GetHomeworkDetailUseCase` lấy deadline trực tiếp từ bản ghi `homework_assignees` của học viên đang đăng nhập.
- **AC 5.2**: DTO trả về cho Frontend tiếp tục chứa trường `deadline` để tương thích 100% với giao diện hiện tại mà không làm vỡ các component Frontend.
