# Feature Specification: Sửa lỗi cập nhật khi bỏ chọn phần game trong chỉnh sửa bài tập

**Feature Branch**: `027-fix-homework-game-uncheck-update`

**Created**: 2026-10-25

**Status**: Draft

**Input**: User description: "Hiện tại tôi chỉnh sửa homework thì bỏ phần game thì hệ thống ko cập nhật đúng /speckit-specify"

---

## Bối cảnh & Vấn đề (Context & Problem Statement)

Khi người quản trị/giảng viên chỉnh sửa một bài tập (Homework) đã có sẵn yêu cầu làm game (`requires_game = True`):
- Trong modal "Chỉnh sửa bài tập", người dùng bỏ chọn checkbox `🎮 Làm game` (chỉ giữ lại `💻 Làm bài tập coding`) và bấm **OK** (Lưu).
- Frontend gửi payload hợp lệ lên backend với `requires_game: false`, `requires_coding: true`.
- Tuy nhiên, sau khi lưu thành công, hệ thống không lưu thay đổi này vào database. Khi tải lại hoặc mở lại modal chỉnh sửa, bài tập vẫn hiển thị là đang yêu cầu làm game (`requires_game` vẫn là `true`).

### Nguyên nhân cốt lõi (Root Cause)
1. **Lớp Repository Backend (`homework_repository.py`)**:
   Hàm `update()` của `HomeworkRepository` khi cập nhật `HomeworkModel` từ `HomeworkEntity` chỉ cập nhật 4 trường:
   ```python
   model.title = homework.title
   model.deadline = homework.deadline
   model.link = homework.link
   model.slug = homework.slug
   ```
   **Hoàn toàn thiếu việc gán cập nhật 2 trường `requires_coding` và `requires_game`**:
   ```python
   model.requires_coding = homework.requires_coding
   model.requires_game = homework.requires_game
   ```
   Do đó, dù `UpdateHomeworkUseCase` đã tính toán đúng `requires_coding` và `requires_game` mới, tầng persistence (SQLAlchemy) vẫn không cập nhật giá trị mới này xuống cơ sở dữ liệu.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bỏ chọn yêu cầu game khi chỉnh sửa bài tập (Priority: P1)

Là một người quản trị hoặc giảng viên, tôi muốn khi chỉnh sửa bài tập và bỏ chọn mục "🎮 Làm game", hệ thống phải lưu chính xác `requires_game = False` vào cơ sở dữ liệu và hiển thị đúng trạng thái sau khi cập nhật.

**Why this priority**: Đây là lỗi cốt lõi ngăn cản người dùng thay đổi cấu hình yêu cầu bài tập của học viên, dẫn đến học viên bị ép nộp game dù giảng viên đã bỏ yêu cầu.

**Independent Test**:
- Tạo một bài tập với cả 2 yêu cầu: `requires_coding = True`, `requires_game = True`.
- Mở modal chỉnh sửa, bỏ chọn `🎮 Làm game` và lưu lại.
- Tải lại dữ liệu (GET API hoặc xem lại modal) -> `requires_game` phải là `False`, `requires_coding` là `True`.

**Acceptance Scenarios**:
1. **Given** bài tập đang có `requires_coding = True` và `requires_game = True`, **When** người dùng chỉnh sửa và bỏ chọn checkbox "🎮 Làm game" rồi bấm Lưu, **Then** hệ thống cập nhật thành công, database lưu `requires_game = False`, và modal mở ra lần sau hiển thị ô checkbox "🎮 Làm game" ở trạng thái uncheck.
2. **Given** bài tập đang có `requires_coding = False` (hoặc True) và `requires_game = True`, **When** người dùng bỏ chọn cả 2 checkbox ("Làm bài tập coding" và "Làm game"), **Then** hệ thống hiển thị thông báo lỗi yêu cầu phải chọn ít nhất một mục và không cho phép submit.

---

### User Story 2 - Thay đổi qua lại giữa các yêu cầu bài tập (Coding & Game) (Priority: P2)

Là một người quản trị, tôi muốn có thể tự do bật/tắt cả `requires_coding` và `requires_game` khi chỉnh sửa bài tập (miễn là thỏa mãn quy tắc nghiệp vụ: có ít nhất 1 yêu cầu được chọn và bài học Quiz có nội dung tương ứng).

**Why this priority**: Đảm bảo tính toàn vẹn 2 chiều: cả việc bỏ chọn coding, bật lại game, hoặc bật cả 2 đều được lưu trữ nhất quán.

**Independent Test**:
- Chỉnh sửa bài tập từ `requires_coding = True, requires_game = False` thành `requires_coding = False, requires_game = True` (với Quiz slug có hỗ trợ game).
- Kiểm tra sau lưu: `requires_coding` trở thành `False`, `requires_game` trở thành `True`.

**Acceptance Scenarios**:
1. **Given** bài tập ban đầu chỉ yêu cầu coding (`requires_coding = True, requires_game = False`), **When** người dùng chỉnh sửa chọn thêm "🎮 Làm game", **Then** hệ thống xác thực Quiz có game và lưu thành công cả 2 cờ là `True`.
2. **Given** bài tập ban đầu yêu cầu cả hai, **When** người dùng bỏ chọn "💻 Làm bài tập coding" (chỉ để "🎮 Làm game"), **Then** hệ thống lưu thành công `requires_coding = False, requires_game = True`.

---

### Edge Cases
- **Quiz validation khi tắt game**: Khi tắt `requires_game` thành `False`, hệ thống KHÔNG được bắt lỗi nếu bài học trên Quiz thiếu câu hỏi game (vì bài tập không còn yêu cầu game nữa).
- **Hủy chọn cả hai**: Khi cả `requires_coding = False` và `requires_game = False`, cả Frontend validation và Backend use case đều phải chặn với thông báo lỗi rõ ràng: *"Vui lòng chọn ít nhất một yêu cầu cho bài tập: 'Làm bài tập coding' hoặc 'Làm game'."*
- **Đồng bộ trạng thái submission học sinh**: Khi bài tập bỏ yêu cầu game, việc tính toán trạng thái nộp bài của học viên (`calculate_submission_status` / `check_overdue`) lập tức dựa trên `requires_game = False`, không còn đánh rớt học sinh vì chưa nộp game.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống Backend (tại `HomeworkRepository.update`) MUST cập nhật đầy đủ các thuộc tính cấu hình yêu cầu bài tập (`requires_coding` và `requires_game`) của `HomeworkModel` từ `HomeworkEntity`.
- **FR-002**: `UpdateHomeworkUseCase` MUST giữ nguyên khả năng nhận diện giá trị boolean tường minh (`requires_coding: bool | None`, `requires_game: bool | None`), cho phép cập nhật giá trị `False` khi người dùng bỏ chọn.
- **FR-003**: Backend MUST xác thực rằng bài tập luôn có ít nhất một trong hai yêu cầu (`effective_coding` hoặc `effective_game`) là `True`.
- **FR-004**: Frontend form modal MUST tiếp tục gửi chính xác giá trị boolean (`requires_coding: boolean`, `requires_game: boolean`) trong payload của `homeworkService.update()`.
- **FR-005**: Unit tests và API integration tests MUST bao phủ kịch bản cập nhật bỏ chọn `requires_game` và `requires_coding` để ngăn chặn hồi quy (regression-prevention).

### Key Entities

- **HomeworkEntity / HomeworkModel**:
  - `id`: Định danh bài tập.
  - `title`: Tiêu đề bài tập.
  - `deadline`: Hạn nộp.
  - `link`: URL bài học trên Quiz.
  - `slug`: Slug bài học Quiz.
  - `requires_coding`: Boolean - cờ yêu cầu hoàn thành phần coding.
  - `requires_game`: Boolean - cờ yêu cầu hoàn thành phần game.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Khi chỉnh sửa bài tập và bỏ chọn checkbox "🎮 Làm game", giá trị `requires_game` trong database được cập nhật thành `False` ngay lập tức (100% các trường hợp).
- **SC-002**: Khi refresh trang hoặc mở lại modal chỉnh sửa bài tập vừa lưu, checkbox "🎮 Làm game" hiển thị đúng trạng thái unchecked.
- **SC-003**: 100% các bài test liên quan đến Homework update (unit tests cho repository, use case, và API integration test) đều vượt qua (Pass).
