# Feature Specification: Đồng Bộ Toàn Diện & Làm Mới Metadata Bài Tập Từ Quiz (Sync Homework & Refresh Quiz Metadata)

**Feature Branch**: `041-sync-homework-refresh-metadata`  
**Created**: 2026-11-01  
**Status**: Draft  
**Input**: Yêu cầu làm mới metadata và danh mục bài tập con khi thực hiện đồng bộ từ Quiz qua `SyncHomeworkFromQuizUseCase`.

---

## 🎯 Bối cảnh & Vấn đề Cần Giải Quyết

Hiện tại trong `SyncHomeworkFromQuizUseCase`:
- Khi giảng viên/admin bấm nút **"Đồng bộ từ Quiz"**, hệ thống chỉ gọi `quiz_api.get_homework_submissions_for_sync()` và `quiz_api.get_game_sessions_for_sync()` để kéo các bài nộp đã có về bảng `homework_submissions`.
- **Hạn chế nghiêm trọng**:
  1. Khi giảng viên thêm bài tập con mới trên hệ thống Quiz nhưng **chưa có học sinh nào nộp**, việc bấm "Đồng bộ từ Quiz" hoàn toàn không kéo được thông tin về bài tập con mới này vì hệ thống chỉ nhìn vào các bài nộp đã phát sinh.
  2. Nếu cấu hình bài học trên Quiz thay đổi (ví dụ: bổ sung thêm Game trắc nghiệm hoặc bài tập Coding mới), `requires_coding` và `requires_game` của bài tập trong database vẫn giữ nguyên giá trị cũ, khiến hệ thống không kích hoạt quét đồng bộ cho phần mới thêm.
  3. Quản trị viên không nhận được thông tin phản hồi về tổng số bài tập con hiện có trên Quiz sau khi đồng bộ.

---

## 👥 User Scenarios & Acceptance Criteria

### User Story 1 - Tự động làm mới cấu hình bài tập từ Quiz khi đồng bộ (Priority: P1) 🎯 MVP

Là một giảng viên/quản trị viên, tôi muốn khi bấm nút "Đồng bộ từ Quiz", hệ thống tự động kiểm tra và cập nhật cấu hình bài tập (`requires_coding`, `requires_game`, metadata) từ Quiz API, để hệ thống luôn phản ánh chính xác trạng thái thực tế của bài học.

**Why this priority**: Đảm bảo cấu hình bài tập không bị lỗi thời so với Quiz, kích hoạt đúng phạm vi đồng bộ cho cả Coding và Game.

**Independent Test**:
- Given một bài tập trong DB ban đầu chỉ bật `requires_coding=True, requires_game=False`.
- Giảng viên thêm game trên Quiz (`has_game=True`).
- When gọi `SyncHomeworkFromQuizUseCase.execute(homework_id)`.
- Then `requires_game` của bài tập trong DB tự động được cập nhật thành `True` và tiến hành đồng bộ cả Game.

**Acceptance Scenarios**:
1. **Given** bài tập có slug hợp lệ trên Quiz, **When** thực thi đồng bộ, **Then** hệ thống gọi `quiz_api.get_lesson_metadata(slug)` và lưu các thay đổi cấu hình (`requires_coding`, `requires_game`) vào database.
2. **Given** bài tập trên Quiz không tồn tại hoặc lỗi mạng khi lấy metadata, **Then** hệ thống ghi nhận warning và fallback tiếp tục đồng bộ các bài nộp hiện có mà không làm gián đoạn tiến trình.

---

### User Story 2 - Nhận diện danh mục bài tập con mới dù chưa có ai nộp (Priority: P2)

Là một học sinh và giảng viên, tôi muốn khi bài tập được đồng bộ từ Quiz, hệ thống nhận diện được tất cả các bài tập con hiện có trên Quiz (kể cả bài mới chưa ai nộp), để bảng trạng thái nộp bài hiển thị đầy đủ các bài tập con cần làm.

**Why this priority**: Giúp học sinh biết mình cần làm những bài tập con nào ngay khi giảng viên vừa giao thêm bài trên Quiz mà chưa ai kịp nộp.

**Independent Test**:
- Giảng viên tạo thêm bài tập con `ex-new` trên Quiz.
- Chưa có học viên nào nộp bài `ex-new`.
- When Admin bấm "Đồng bộ từ Quiz".
- Then gọi `quiz_api.get_lesson_exercises(slug)` xác nhận danh mục bài tập con đã bao gồm `ex-new`, sẵn sàng cho màn hình báo cáo nộp bài hiển thị.

**Acceptance Scenarios**:
1. **Given** bài học có các bài tập con trên Quiz, **When** đồng bộ, **Then** hệ thống truy vấn `quiz_api.get_lesson_exercises(slug)` và thống kê chính xác số lượng bài tập con hiện tại.
2. **Given** kết quả trả về từ `SyncHomeworkFromQuizUseCase`, **Then** chứa thông tin metadata tổng quan: `coding_exercises_count`, `game_question_count`, `has_coding`, `has_game`.

---

### User Story 3 - Phản hồi kết quả đồng bộ chi tiết và minh bạch (Priority: P3)

Là một giảng viên/admin, tôi muốn xem kết quả chi tiết sau khi bấm đồng bộ (bao gồm tổng số bài tập con trên Quiz, số bài nộp mới, số bài nộp cập nhật), để an tâm rằng hệ thống đã nhận diện đầy đủ bài tập mới.

**Why this priority**: Cải thiện trải nghiệm quản trị (UX) và tính minh bạch của tác vụ đồng bộ thủ công.

**Independent Test**:
- Bấm đồng bộ một bài tập và kiểm tra payload trả về chứa đầy đủ các trường `coding_exercises_count`, `game_question_count`, `synced_coding_count`, `synced_game_count`, `message`.

**Acceptance Scenarios**:
1. **Given** đồng bộ hoàn tất, **When** kiểm tra response dictionary, **Then** có đầy đủ thông tin về số lượng bài tập con trên Quiz và số lượt nộp bài đã đồng bộ.

---

## 📋 Functional Requirements

- **FR-001**: `SyncHomeworkFromQuizUseCase` bắt buộc gọi `quiz_api.get_lesson_metadata(slug)` ở đầu quy trình đồng bộ để lấy trạng thái mới nhất (`has_coding`, `has_game`, `coding_count`, `game_question_count`).
- **FR-002**: Nếu metadata trả về có sự thay đổi về yêu cầu (`has_coding != homework.requires_coding` hoặc `has_game != homework.requires_game`), `SyncHomeworkFromQuizUseCase` phải cập nhật lại `HomeworkEntity` và lưu xuống database qua `homework_repo.save()`.
- **FR-003**: `SyncHomeworkFromQuizUseCase` gọi `quiz_api.get_lesson_exercises(slug)` để xác nhận danh sách bài tập con mới nhất từ Quiz API.
- **FR-004**: Quy trình đồng bộ bài nộp Coding & Game phải sử dụng các cờ `requires_coding` và `requires_game` đã được cập nhật mới nhất từ metadata.
- **FR-005**: Kết quả trả về của `execute()` phải bổ sung các trường metadata:
  - `coding_exercises_count`: số lượng bài tập con coding trên Quiz.
  - `game_questions_count`: số lượng câu hỏi game trên Quiz.
  - `requires_coding`: trạng thái yêu cầu coding sau đồng bộ.
  - `requires_game`: trạng thái yêu cầu game sau đồng bộ.

---

## 🎯 Non-Functional & Success Criteria

- **SC-001**: 100% các bài tập sau khi bấm "Đồng bộ từ Quiz" đều được cập nhật cấu hình mới nhất từ Quiz API.
- **SC-002**: Trường hợp Quiz API bị gián đoạn hoặc không có metadata, hệ thống phải fallback an toàn không gây lỗi 500 (Fail-Safe).
- **SC-003**: Thời gian thực thi `SyncHomeworkFromQuizUseCase` tăng không quá 500ms khi bổ sung các cuộc gọi API làm mới metadata.
