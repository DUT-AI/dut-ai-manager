# Feature Specification: Tối Ưu Hóa Tốc Độ Tải Danh Sách Bài Nộp Chi Tiết Bài Tập (DB-First Submission Status)

**Feature Branch**: `017-optimize-homework-submission-status`

**Created**: 2026-10-18

**Status**: Draft

**Input**: User description: "Tôi muốn giảm thời gian phản hồi xuống bằng các phương án bạn đề xuất trên (Bỏ qua gọi Quiz Game khi bài không yêu cầu Game, Chạy song song asyncio.gather, Áp dụng DB-First hoàn toàn cho GetHomeworkSubmissionStatusUseCase)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Người Quản Trị Tải Chi Tiết Bài Nộp Tức Thì (Priority: P1)

Người quản trị (Admin/Teacher) khi vào xem chi tiết bài tập bất kỳ (ví dụ bài tập GAN gen1 ID 72) tại trang quản trị mong muốn danh sách bài nộp hiển thị ngay lập tức mà không phải chờ đợi loading quay vòng nhiều giây.

**Why this priority**: Đây là trải nghiệm trực tiếp hàng ngày của người quản trị. Việc trang load 10-15s gây gián đoạn công việc quản lý và tạo cảm giác hệ thống bị đơ/lag.

**Independent Test**:
- Truy cập trang `https://manage.dutai.io.vn/dashboard/homeworks/72` hoặc gọi `GET /api/v1/homeworks/72/submission-status`.
- Thời gian phản hồi hoàn tất dưới 500ms với đầy đủ số liệu thống kê danh sách học viên nộp bài, phân loại bài con, trạng thái hoàn thành.

**Acceptance Scenarios**:

1. **Given** bài tập chỉ yêu cầu Coding (`requires_coding=True`, `requires_game=False`), **When** người quản trị tải trang trạng thái nộp bài, **Then** hệ thống KHÔNG thực hiện bất kỳ cuộc gọi mạng nào đến endpoint Game của Quiz API.
2. **Given** các bài nộp đã được đồng bộ vào cơ sở dữ liệu nội bộ (`homework_submissions`), **When** người quản trị xem trang chi tiết bài tập, **Then** hệ thống ưu tiên đọc 100% dữ liệu từ cơ sở dữ liệu nội bộ, phản hồi kết quả ngay lập tức mà không bị nghẽn mạng do Quiz API bên ngoài.
3. **Given** bài tập có các bài tập con (sub-exercises), **When** trả về danh sách, **Then** danh mục bài tập con và tỉ lệ hoàn thành của từng bài tập con hiển thị đầy đủ, chính xác dựa trên lịch sử bài nộp đã lưu.

---

### User Story 2 - Quản Trị Chủ Động Đồng Bộ Dữ Liệu Từ Quiz Khi Cần Thiết (Priority: P2)

Khi học viên vừa nộp bài trên Quiz và người quản trị muốn cập nhật kết quả mới nhất ngay tức khắc, người quản trị chủ động bấm nút "Đồng bộ từ Quiz". Hệ thống mới kích hoạt gọi Quiz API để kéo dữ liệu mới nhất về lưu vào DB.

**Why this priority**: Đảm bảo dữ liệu luôn có thể cập nhật kịp thời khi có bài nộp mới, đồng thời tách biệt hoàn toàn giữa luồng đọc (Read: siêu nhanh, từ DB) và luồng đồng bộ (Sync: theo yêu cầu chủ động).

**Independent Test**:
- Bấm nút "Đồng bộ từ Quiz" trên trang chi tiết bài tập.
- API `POST /api/v1/homeworks/{id}/sync` kéo các bản ghi nộp bài mới từ Quiz về DB và tự động làm mới giao diện hiển thị kết quả mới.

**Acceptance Scenarios**:

1. **Given** người quản trị bấm nút "Đồng bộ từ Quiz", **When** hệ thống gọi Quiz API đồng bộ, **Then** chỉ gọi các dịch vụ tương ứng với loại bài tập (`requires_coding` -> sync coding, `requires_game` -> sync game) và chạy song song để tối ưu thời gian đồng bộ.
2. **Given** Quiz API gặp sự cố hoặc timeout khi người dùng chỉ xem trang (không bấm sync), **Then** trang chi tiết bài nộp vẫn mở bình thường với dữ liệu hiện có trong DB thay vì bị treo hoặc báo lỗi 500/timeout.

---

## Edge Cases

- **Bài tập chưa có bản ghi nộp nào trong DB và Quiz API không phản hồi**: Hệ thống hiển thị danh sách bài nộp rỗng một cách an toàn, không làm crash trang.
- **Bài tập yêu cầu cả Coding và Game (`requires_coding=True` và `requires_game=True`)**: Nếu cần gọi thông tin bổ sung, các tác vụ phải được thực thi đồng thời (song song) thay vì nối tiếp, tổng thời gian chờ không vượt quá thời gian của tác vụ lâu nhất.
- **Bài tập không có cấu trúc bài con được định nghĩa trước**: Hệ thống tự động suy diễn danh sách bài tập con từ các bản ghi nộp bài thực tế trong cơ sở dữ liệu nội bộ.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001 (Loại bỏ gọi Quiz API dư thừa theo cấu hình bài tập)**:
  - Hệ thống KHÔNG ĐƯỢC gọi bất kỳ endpoint nào liên quan đến Game nếu bài tập có `requires_game = False`.
  - Hệ thống KHÔNG ĐƯỢC gọi bất kỳ endpoint nào liên quan đến Coding nếu bài tập có `requires_coding = False`.
- **FR-002 (Kiến trúc DB-First cho Endpoint Trạng Thái Bài Nộp)**:
  - Endpoint `GET /api/v1/homeworks/{homework_id}/submission-status` PHẢI ưu tiên đọc cấu trúc bài tập và trạng thái nộp bài của học viên trực tiếp từ bảng dữ liệu nội bộ `homework_submissions` và danh sách học viên được giao (`homework_assignees`).
  - Không chặn (block) request của người dùng bằng các cuộc gọi HTTP mạng ra dịch vụ Quiz bên ngoài mỗi khi tải trang.
- **FR-003 (Chạy song song các tác vụ gọi ngoài nếu có)**:
  - Trong bất kỳ trường hợp nào cần gọi thông tin từ Quiz API (như lấy metadata bài tập hoặc đồng bộ), các cuộc gọi mạng PHẢI được thực thi song song (`asyncio.gather`), không được dùng `await` tuần tự nối tiếp.
- **FR-004 (Bảo toàn 100% hợp đồng dữ liệu DTO)**:
  - Dữ liệu trả về của DTO `HomeworkSubmissionStatusResponse` (bao gồm `coding`, `game`, `coding_exercises`, `students`, `submitted`, `not_submitted`) PHẢI giữ nguyên cấu trúc và ý nghĩa dữ liệu để Frontend không phải thay đổi hay phát sinh lỗi hiển thị.
- **FR-005 (Đảm bảo cơ chế tính toán hạn nộp & bài nộp muộn)**:
  - Logic xét nộp trễ (`is_late`), gia hạn nộp bài (`permission_requests`) và trạng thái hoàn thành (`COMPLETED`, `PARTIALLY_SUBMITTED`, `NOT_SUBMITTED`) tiếp tục hoạt động chính xác dựa trên dữ liệu thời gian nộp bài trong DB.

### Key Entities

- **Homework**: Thực thể bài tập, chứa cờ cấu hình `requires_coding` và `requires_game`, hạn nộp `deadline`, danh sách học viên `assignee_ids`.
- **HomeworkSubmission**: Thực thể bài nộp đã lưu trong hệ thống, chứa `user_id`, `exercise_id`, `exercise_title`, `submission_type`, `is_passed`, `score`, `submitted_at`.
- **HomeworkSubmissionStatusResponse**: Mô hình dữ liệu trả về cho giao diện chi tiết, tổng hợp trạng thái nộp bài phân loại theo bài tập con, coding, game và từng cá nhân học viên.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Thời gian phản hồi của endpoint xem chi tiết trạng thái nộp bài giảm từ hơn 10 giây xuống dưới 500 mili-giây đối với các bài tập đã có dữ liệu.
- **SC-002**: Tỉ lệ tải trang chi tiết bài nộp thành công đạt 100% ngay cả khi dịch vụ Quiz bên ngoài bị trễ mạng hoặc tạm thời ngắt kết nối.
- **SC-003**: 100% người dùng xem chi tiết bài tập không còn gặp hiện tượng giao diện bị đơ/chờ loading trên 3 giây.
- **SC-004**: Độ chính xác của trạng thái nộp bài (đã nộp, chưa nộp, bài nộp muộn) được giữ nguyên vẹn 100% so với trước khi tối ưu.

---

## Assumptions

- Toàn bộ bài nộp của học viên đã và đang được ghi nhận vào cơ sở dữ liệu nội bộ qua webhook từ Quiz hoặc qua chức năng đồng bộ ("Đồng bộ từ Quiz").
- Khi có bài nộp mới phát sinh ngoài luồng webhook, người quản trị có thể kích hoạt nút đồng bộ bất cứ lúc nào để cập nhật dữ liệu vào DB.
- Cấu hình bài tập (`requires_coding`, `requires_game`) phản ánh đúng nhu cầu học tập của bài tập đó.
