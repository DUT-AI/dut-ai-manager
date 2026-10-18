# Feature Specification: Đồng Bộ và Hiển Thị Chính Xác Trạng Thái Trắc Nghiệm Game Trên My Homeworks

**Feature Branch**: `016-fix-my-homeworks-game-submission-status`

**Created**: 2026-10-18

**Status**: Draft

**Input**: User description: "hãy check lại giúp tôi là ở route my-homeworks ở FE, người dùng đã làm game rồi nhưng bị lỗi vẫn hiển thị là chưa làm game"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Hiển thị trạng thái Game đã hoàn thành khi mở trang Bài tập của tôi (Priority: P1)

Khi học viên đã hoàn thành trắc nghiệm Game trên nền tảng Quiz, học viên truy cập trang `/dashboard/my-homeworks` (hoặc sau khi kích hoạt Đồng bộ / nhận Webhook), hệ thống hiển thị chính xác tag "Game: Đã xong", trạng thái tổng thể là "Đã hoàn thành toàn bộ" (nếu bài có cả Coding & Game và Coding cũng đã nộp), thay vì hiển thị "Game: Chưa chơi" hay cảnh báo "Hoàn thành 1/2 • Thiếu Game".

**Why this priority**: Đây là luồng nghiệp vụ cốt lõi ảnh hưởng trực tiếp đến trải nghiệm của học viên; việc học viên đã chơi game đạt chuẩn nhưng hệ thống vẫn báo "Chưa chơi" hoặc phạt trễ hạn gây hoang mang và khiếu nại.

**Independent Test**:
- Giả lập một bài tập có yêu cầu cả Coding và Game.
- Học viên đã nộp Coding và hoàn thành Game Session (đạt điều kiện hoàn thành bài).
- Mở trang `my-homeworks`: Thẻ bài tập hiển thị màu xanh hoàn thành, badge "Đã hoàn thành toàn bộ", badge Coding "Đã nộp", badge Game "Đã xong", nút hành động chuyển thành "Xem bài nộp trên Quiz".

**Acceptance Scenarios**:

1. **Given** học viên đã nộp Coding và đã hoàn thành Game trên Quiz,
   **When** học viên xem bài tập trên `/dashboard/my-homeworks`,
   **Then** hệ thống ghi nhận `game_submitted = True`, `is_submitted = True`, không còn hiển thị thông báo thiếu Game.

2. **Given** học viên mới chỉ hoàn thành Game mà chưa nộp Coding,
   **When** học viên xem bài tập trên `/dashboard/my-homeworks`,
   **Then** bài tập hiển thị tag "Game: Đã xong", tag "Coding: Chưa nộp", trạng thái "Hoàn thành 1/2 • Thiếu Coding", và thông báo nhắc nhở làm tiếp phần Coding.

3. **Given** học viên chỉ mới làm dở dang hoặc chưa đạt tiêu chuẩn hoàn thành game (chưa nộp / chưa xong toàn bộ câu hỏi),
   **When** học viên xem bài tập trên `/dashboard/my-homeworks`,
   **Then** hệ thống hiển thị tag "Game: Chưa chơi" và hướng dẫn tiếp tục làm bài.

---

### User Story 2 - Tự động đồng bộ và đồng bộ thủ công kết quả Game từ Quiz (Priority: P2)

Học viên vừa hoàn thành bài Game trên Quiz có thể bấm nút "Đồng bộ" trên thẻ bài tập, hoặc hệ thống tự động nhận webhook từ Quiz để lưu bản ghi bài nộp Game vào cơ sở dữ liệu. Sau khi đồng bộ, giao diện cập nhật ngay lập tức trạng thái "Game: Đã xong" mà không cần reload trang.

**Why this priority**: Cung cấp cơ chế tự phục hồi và đối soát tức thì cho học viên khi vừa làm xong game mà webhook chưa về tới.

**Independent Test**:
- Bấm nút "Đồng bộ" trên thẻ bài tập có yêu cầu Game.
- Backend kéo kết quả session hoặc leaderboard từ Quiz API về DB.
- Query client invalidate cache và thẻ bài tập chuyển sang "Game: Đã xong".

**Acceptance Scenarios**:

1. **Given** học viên vừa chơi xong game trên Quiz và thẻ bài tập đang hiển thị "Game: Chưa chơi",
   **When** học viên bấm nút "Đồng bộ",
   **Then** hệ thống gọi API đồng bộ, thông báo thành công và chuyển ngay tag sang "Game: Đã xong".

2. **Given** hệ thống Quiz gửi webhook sự kiện hoàn thành game qua `/api/v1/homeworks/webhook/submission`,
   **When** webhook được xử lý thành công với `type=GAME` và `is_passed=True`,
   **Then** bản ghi được lưu/cập nhật vào bảng `homework_submissions`, các lần đọc tiếp theo từ `/api/v1/homeworks/me` trả về `game_submitted = True`.

---

### Edge Cases

- **Game hoàn thành nhưng điểm số 0 hoặc chưa làm hết câu hỏi**: Tiêu chí đánh giá `is_passed` phải nhất quán giữa việc đồng bộ qua `sessions-for-sync` (kiểm tra `is_completed`) và `leaderboard` (kiểm tra `answered_questions >= total_questions`). Nếu học viên chỉ mở game lên rồi thoát (chưa hoàn thành), hệ thống không được tính là `game_submitted`.
- **Slug của bài tập có sự sai lệch hoặc định dạng đường dẫn khác nhau**: Link bài tập có thể là URL dạng `/lessons/{slug}`, `/game/{slug}` hoặc `/homeworks/{slug}`. Quá trình tra cứu webhook và đồng bộ phải giải quyết đúng slug bài tập để mapping chính xác với `homework_id`.
- **Học viên chưa bấm đồng bộ và webhook bị trễ**: Thẻ bài tập cần hiển thị rõ nút "Đồng bộ" kèm tooltip hướng dẫn để người dùng chủ động kéo kết quả mới nhất.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống Backend PHẢI lưu trữ và cập nhật trạng thái nộp bài Game của học viên vào bảng `homework_submissions` với `submission_type = GAME` và `is_passed = True` khi nhận webhook hoặc khi thực hiện đồng bộ từ Quiz.
- **FR-002**: Use case `GetUserHomeworksUseCase` (`GET /api/v1/homeworks/me`) PHẢI đánh giá trạng thái `game_submitted = True` khi tồn tại ít nhất 1 bản ghi `GAME` hợp lệ (`is_passed == True`) trong cơ sở dữ liệu của người dùng cho bài tập đó.
- **FR-003**: Endpoint đồng bộ (`POST /api/v1/homeworks/{homework_id}/sync`) PHẢI đồng bộ đầy đủ các phiên chơi game đạt điều kiện hoàn thành từ Quiz API (`get_game_sessions_for_sync` và fallback `get_game_leaderboard`), lưu vào `homework_submissions` với cờ `is_passed = True`.
- **FR-004**: Frontend `HomeworkCard` trên route `/dashboard/my-homeworks` PHẢI hiển thị tag `Game: Đã xong` (màu xanh lá) khi `homework.game_submitted` mang giá trị `true`, và `Game: Chưa chơi` (màu xám / đỏ nếu quá hạn) khi `false`.
- **FR-005**: Thẻ bài tập chỉ được hiển thị tổng thể là `Đã hoàn thành toàn bộ` khi thỏa mãn đồng thời:
  - Nếu bài có yêu cầu Coding: `coding_submitted == True`.
  - Nếu bài có yêu cầu Game: `game_submitted == True`.
- **FR-006**: Khi học viên bấm nút "Đồng bộ" trên thẻ bài tập, Frontend PHẢI invalidate cache của query `['homeworks', 'me']` và cập nhật lại giao diện người dùng ngay sau khi API phản hồi thành công.

### Key Entities

- **Homework**: Thực thể bài tập được giao, chứa các thuộc tính cấu hình yêu cầu: `requires_coding` (hoặc `has_coding`), `requires_game` (hoặc `has_game`), `deadline`, `slug`, `link`.
- **HomeworkSubmission**: Thực thể lưu trữ lịch sử nộp bài của học viên, gồm: `homework_id`, `user_id`, `submission_type` (`CODING` hoặc `GAME`), `is_passed` (boolean), `submitted_at`, và thông tin chi tiết phiên chơi (`details`).
- **SubmissionEvaluation**: Đối tượng tính toán trạng thái tổng hợp của bài tập cho 1 học viên, xác định `is_submitted`, `is_overdue`, `coding_submitted`, `game_submitted`, `uncompleted_items`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% học viên đã hoàn thành game trên Quiz khi truy cập `/dashboard/my-homeworks` (hoặc sau khi bấm "Đồng bộ") nhìn thấy đúng trạng thái `Game: Đã xong`.
- **SC-002**: Không xảy ra trường hợp bài tập có đủ cả Coding và Game đã hoàn thành nhưng vẫn bị gán nhãn `Hoàn thành 1/2 • Thiếu Game`.
- **SC-003**: Tốc độ phản hồi giao diện danh sách bài tập duy trì mượt mà (< 200ms) nhờ cơ chế đọc dữ liệu hoàn toàn từ cơ sở dữ liệu nội bộ (DB-First).

## Assumptions

- Học viên hoàn thành game trên Quiz với tài khoản trùng khớp `user_id` trong hệ thống DUT AI Manager.
- Hệ thống Quiz cung cấp API phiên chơi game (`sessions-for-sync` hoặc `leaderboard`) có chứa `user_id` và đánh dấu `is_completed: true` khi hoàn thành tất cả câu hỏi của trò chơi.
- Khi người dùng làm bài trên Quiz, hệ thống Quiz hỗ trợ gửi webhook về `/api/v1/homeworks/webhook/submission` hoặc người dùng có thể kích hoạt nút "Đồng bộ" trên giao diện bài tập.

