# Feature Specification: Quản Lý Và Lưu Vết Chi Tiết Lịch Sử Từng Bài Tập Coding Của Lesson

**Feature Branch**: `008-detailed-exercise-history`

**Created**: 2026-10-06

**Status**: Draft

**Input**: User description: "Hãy thiết kế lại bên manage để có thể lưu lại lịch sử chi tiết của từng bài tập coding của 1 lesson ( 1 lesson có nhiều bài tập coding ) , thiết kế cả quiz và manage luôn, dùng Pydantic Model để validate dữ liệu trao đổi 2 bên"

---

## Bối Cảnh & Vấn Đề

Hiện tại, trong hệ thống quản lý học tập:
- **DUT-AI Quiz**: Một bài học (`Lesson`) có thể chứa nhiều ($N$) bài tập coding (`HomeworkEntity` gắn với `lesson_id`, mỗi bài có `id` là UUID, tiêu đề, mô tả và file đính kèm riêng).
- **DUT-AI Manager**: Quản lý bài tập theo từng bài học thông qua thuộc tính `slug` (`lesson_slug`).
- **Lỗ hổng hiện tại**:
  1. Khi học viên nộp bất kỳ **1 bài tập coding nào** trong lesson, Quiz chỉ gửi webhook chứa `lesson_slug` chung chung và API đối soát `/completed-members` chỉ đếm `submission_count > 0` trên toàn bộ lesson.
  2. Manager ghi nhận bài nộp cho cả `Homework` của lesson và coi như học viên đã hoàn thành (Submitted) phần Coding, dù học viên mới chỉ làm $1/N$ bài tập và bỏ qua các bài tập còn lại.
  3. Manager không lưu được lịch sử nộp chi tiết của từng bài tập con (tên bài, mã bài tập `exercise_id`, điểm số, số lần nộp, trạng thái pass/fail).

Tính năng này tái cấu trúc toàn diện cơ chế đồng bộ, lưu vết và hiển thị bài nộp giữa **DUT-AI Quiz** và **DUT-AI Manager**, đảm bảo theo dõi chính xác từng bài tập coding con với dữ liệu được kiểm thực chặt chẽ bằng Pydantic Models.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ghi nhận và lưu vết chi tiết từng bài tập coding con qua Webhook (Priority: P1)

Khi học viên nộp bài cho một bài tập coding cụ thể trên Quiz, Quiz tự động gửi Webhook sang Manager với payload chi tiết chứa mã định danh bài tập con (`exercise_id`), tiêu đề bài tập (`exercise_title`), mã bài nộp (`submission_id`), điểm số, trạng thái và thời gian nộp. Manager xác thực payload bằng Pydantic Model và lưu/cập nhật bản ghi bài nộp tương ứng với bài tập con đó vào cơ sở dữ liệu (Idempotent Append/Upsert).

**Why this priority**: Đây là kênh dữ liệu thời gian thực cốt lõi để Manager nhận biết học viên đã nộp bài tập coding nào, đảm bảo không bị ghi nhận nhầm lẫn giữa các bài tập trong cùng một lesson.

**Independent Test**: Gửi payload Webhook mô phỏng nộp bài tập A và bài tập B của cùng một lesson. Kiểm tra database của Manager có 2 bản ghi submission riêng biệt chứa đúng `exercise_id` và thông tin chi tiết.

**Acceptance Scenarios**:

1. **Given** học viên nộp bài cho bài tập coding A (ID: `uuid-a`) của bài học `deep-learning-intro`, **When** Quiz gửi webhook sang Manager, **Then** Manager xác thực thành công và lưu bản ghi submission với `exercise_id="uuid-a"` và `exercise_title="Bài tập 1: Forward Propagation"`.
2. **Given** học viên nộp lại bài tập coding A để cải thiện điểm, **When** Quiz gửi webhook bài nộp mới (attempt 2), **Then** Manager cập nhật bản ghi submission tương ứng với `attempt_number=2`, điểm số mới và thời gian nộp mới mà không gây duplicate hay lỗi dữ liệu.
3. **Given** webhook gửi đến với dữ liệu thiếu trường bắt buộc hoặc sai định dạng kiểu dữ liệu, **When** Manager xử lý, **Then** Pydantic Model từ chối dữ liệu (HTTP 422/Bad Request), ghi log cảnh báo và không làm sai lệch dữ liệu hiện có.

---

### User Story 2 - Theo dõi tiến độ chi tiết từng bài tập con trên Manager (Priority: P1)

Giảng viên / Quản trị viên khi xem chi tiết trạng thái nộp bài của một bài tập trên Manager có thể thấy:
1. Danh sách đầy đủ $N$ bài tập coding con của bài học (lấy từ Quiz).
2. Trạng thái nộp bài của từng học viên theo từng bài tập con:
   - Hoàn thành đầy đủ: Đã nộp đủ $N/N$ bài tập.
   - Hoàn thành một phần: Đã nộp $k/N$ bài tập (kèm danh sách bài đã nộp và bài còn thiếu).
   - Chưa nộp: Chưa nộp bất kỳ bài tập nào ($0/N$).
3. Chi tiết từng bài nộp của học viên: Điểm số, thời gian nộp, trạng thái trễ hạn (nộp sau deadline của bài học).

**Why this priority**: Cung cấp bức tranh toàn diện và chính xác cho giảng viên về tình hình học tập của lớp, phát hiện ngay các học viên chỉ làm một phần bài tập.

**Independent Test**: Tạo một bài học có 3 bài tập coding trên Quiz. Cho học viên 1 nộp đủ 3 bài, học viên 2 nộp 1 bài, học viên 3 chưa nộp bài nào. Gọi API lấy trạng thái nộp bài trên Manager và kiểm tra cấu trúc phản hồi phân loại chính xác 3 trạng thái.

**Acceptance Scenarios**:

1. **Given** bài học có 3 bài tập coding, **When** gọi `GET /homeworks/{id}/submission-status`, **Then** Manager trả về danh sách các bài tập con (`exercises`) và ma trận tiến độ nộp bài của từng học viên cho từng bài tập.
2. **Given** học viên mới chỉ nộp 2/3 bài tập khi đã quá deadline, **When** kiểm tra trạng thái, **Then** học viên được đánh dấu là `PARTIALLY_SUBMITTED` (hoặc phân loại chưa hoàn thành đầy đủ) và các bài chưa nộp được đánh dấu `is_late=true`.
3. **Given** học viên đã nộp đủ 3/3 bài tập trước deadline, **When** kiểm tra trạng thái, **Then** học viên được đánh dấu là `COMPLETED` cho toàn bộ phần coding.

---

### User Story 3 - Đồng bộ dữ liệu lịch sử bài nộp chi tiết (Sync API) giữa Quiz và Manager (Priority: P2)

Khi Manager thực hiện đồng bộ (Sync/Rescan) dữ liệu từ Quiz (qua API hoặc tác vụ chạy ngầm), Quiz cung cấp endpoint trả về danh sách chi tiết toàn bộ bài tập con và toàn bộ lịch sử nộp bài của bài học đó. Manager nạp và đối soát toàn bộ bản ghi theo từng `exercise_id`, đảm bảo cơ sở dữ liệu Manager luôn đồng nhất với Quiz ngay cả khi webhook gặp sự cố mạng tạm thời.

**Why this priority**: Đảm bảo tính nhất quán (data consistency) và khả năng phục hồi dữ liệu tự động giữa hai hệ thống độc lập.

**Independent Test**: Tắt webhook tạm thời, nộp 2 bài tập trên Quiz, sau đó kích hoạt Sync trên Manager và xác nhận dữ liệu trên Manager được cập nhật đầy đủ và chính xác.

**Acceptance Scenarios**:

1. **Given** Manager kích hoạt đồng bộ bài học `lesson_slug`, **When** gọi API đồng bộ của Quiz, **Then** Quiz trả về cấu trúc danh sách bài tập con và toàn bộ bài nộp kèm `exercise_id`, `score`, `status`, `submitted_at`.
2. **Given** dữ liệu trả về từ Quiz, **When** Manager xử lý qua Pydantic Sync Schema, **Then** Manager cập nhật bảng `homework_submissions` tương ứng cho từng bài tập con một cách an toàn và idempotent.

---

### User Story 4 - Quét bài tập quá hạn (Overdue Checker) dựa trên tiêu chí hoàn thành tất cả bài tập (Priority: P2)

Tác vụ kiểm tra quá hạn định kỳ (`CheckOverdueHomeworkUseCase`) trên Manager kiểm tra xem học viên đã nộp **toàn bộ** các bài tập coding con của bài học hay chưa. Nếu học viên chưa nộp hoặc chỉ nộp một phần khi đã quá hạn (và không có yêu cầu hoãn được duyệt), hệ thống sẽ phát sự kiện `HomeworkOverdueDetected` để ghi nhận vi phạm / gửi thông báo nhắc nhở.

**Why this priority**: Đảm bảo chế tài kỷ luật học tập chính xác, tránh trường hợp học viên nộp 1 bài để "lách luật" quá hạn cho cả lesson.

**Independent Test**: Chạy `CheckOverdueHomeworkUseCase` với học viên chỉ nộp 1/2 bài khi đã qua hạn. Kiểm tra sự kiện quá hạn được kích hoạt chính xác cho học viên đó.

**Acceptance Scenarios**:

1. **Given** bài học có 2 bài tập coding và đã qua hạn nộp, **When** học viên A chỉ mới nộp 1 bài, **Then** hệ thống xác định học viên A chưa hoàn thành và phát sự kiện `HomeworkOverdueDetected`.
2. **Given** học viên B đã nộp đủ 2/2 bài trước hạn nộp, **When** hệ thống quét quá hạn, **Then** học viên B được bỏ qua và không bị tính vi phạm.

---

### Edge Cases

- **Lesson không có bài tập coding nào (`coding_count == 0`)**: Hệ thống tự động bỏ qua kiểm tra coding và chỉ kiểm tra phần Game nếu có yêu cầu.
- **Giảng viên thêm bài tập coding mới vào Lesson sau khi học viên đã nộp các bài cũ**:
  - Khi Sync hoặc truy vấn trạng thái, danh sách bài tập con được cập nhật số lượng mới ($N+1$).
  - Học viên trước đó đã nộp đủ $N$ bài sẽ chuyển sang trạng thái nộp $N/(N+1)$ bài (cần làm thêm bài mới).
- **Học viên nộp bài nhiều lần cho cùng 1 bài tập con**:
  - Quiz gửi webhook với `attempt_number` tăng dần.
  - Manager cập nhật thông tin mới nhất (điểm cao nhất / lần nộp cuối) hoặc lưu vết lịch sử theo thiết kế idempotent upsert.
- **Lỗi mạng hoặc Timeout khi gọi Quiz API**:
  - Manager fallback sử dụng dữ liệu đã lưu trong bảng `homework_submissions` của database nội bộ để phản hồi cho giao diện và tác vụ background, không để hệ thống bị treo.

---

## Requirements *(mandatory)*

### Functional Requirements

#### 1. Phía DUT-AI Quiz (`apps/api`):
- **FR-QUIZ-001**: Quiz PHẢI cung cấp endpoint `GET /api/v1/lessons/{lesson_slug}/exercises` trả về danh sách chi tiết các bài tập coding con thuộc lesson (`id`, `lesson_id`, `title`, `description`, `created_at`, `has_attachment`).
- **FR-QUIZ-002**: Quiz PHẢI cập nhật Webhook dispatch trong `submit_homework_uc.py` (và grading service nếu có) gửi đầy đủ thông tin bài tập con: `exercise_id` (UUID của bài tập), `exercise_title`, `submission_id`, `attempt_number`, `score`, `is_passed`, `submitted_at`, `original_filename`.
- **FR-QUIZ-003**: Quiz PHẢI cập nhật endpoint `GET /api/v1/homeworks/{lesson_slug}/completed-members` hoặc cung cấp endpoint chuyên biệt trả về trạng thái hoàn thành chỉ khi học viên đã nộp đủ tất cả bài tập coding con đang kích hoạt (`count(DISTINCT homework_id) == count_active_homeworks`).
- **FR-QUIZ-004**: Quiz PHẢI chuẩn hóa DTO đồng bộ `HomeworkSubmissionSyncOutDTO` chứa `homework_id` (exercise_id) và `homework_title` (exercise_title) cho endpoint `GET /api/v1/homeworks/{lesson_slug}/submissions-for-sync`.

#### 2. Phía DUT-AI Manager (`backend/app`):
- **FR-MGR-001**: Database schema của Manager (`homework_submissions`) PHẢI bổ sung các trường:
  - `exercise_id`: `String(64)` (nullable cho bài nộp loại GAME hoặc bài cũ, lưu UUID của bài tập bên Quiz).
  - `exercise_title`: `String(255)` (nullable, tiêu đề bài tập con).
  - `score`: `Float` (nullable, điểm số bài nộp).
  - `attempt_number`: `Integer` (mặc định 1).
  - Tạo composite index: `ix_hw_submissions_hw_user_exercise` trên `(homework_id, user_id, exercise_id)`.
- **FR-MGR-002**: Manager PHẢI định nghĩa các Pydantic Models để validate dữ liệu nhận từ Webhook và dữ liệu gọi từ Quiz API:
  - `ExerciseItemDTO`: Thông tin 1 bài tập con từ Quiz.
  - `HomeworkSubmissionWebhookIn`: Payload Webhook nhận từ Quiz (hỗ trợ cả CODING có `exercise_id` và GAME).
  - `HomeworkSubmissionSyncItemDTO`: Schema đồng bộ bài nộp chi tiết từ Quiz.
  - `UserExerciseProgressDTO`: Trạng thái nộp của 1 học viên đối với 1 bài tập con cụ thể.
  - `UserOverallProgressDTO`: Trạng thái tổng thể của học viên ($k/N$ bài tập, điểm trung bình, trạng thái hoàn thành).
  - `HomeworkDetailedSubmissionStatusResponse`: Response trả về cho API trạng thái nộp bài.
- **FR-MGR-003**: `RecordHomeworkSubmissionUseCase` PHẢI lưu vết bài nộp theo `(homework_id, user_id, exercise_id)` và cập nhật điểm/lần nộp nếu đã tồn tại bản ghi của cùng bài tập con.
- **FR-MGR-004**: `GetHomeworkSubmissionStatusUseCase` PHẢI truy vấn danh sách bài tập con từ Quiz API (hoặc cache), kết hợp với dữ liệu bài nộp trong database nội bộ để trả về ma trận tiến độ nộp bài chi tiết theo từng bài tập con.
- **FR-MGR-005**: `CheckOverdueHomeworkUseCase` PHẢI coi học viên là đã hoàn thành phần coding khi và chỉ khi học viên đã nộp đủ $100\%$ các bài tập coding con của lesson đó.
- **FR-MGR-006**: Manager PHẢI cung cấp migration script Alembic tương thích ngược, không làm mất dữ liệu submission cũ.

---

### Data Contracts & Pydantic Models *(Trao đổi giữa 2 hệ thống)*

#### 1. Webhook Payload Schema (`Quiz -> Manager`)
```python
class HomeworkSubmissionWebhookIn(BaseModel):
    lesson_slug: str
    user_id: int
    type: SubmissionType  # CODING hoặc GAME
    submitted_at: datetime
    is_passed: bool = True
    
    # Trường chi tiết cho Coding Exercise
    exercise_id: str | None = None          # UUID bài tập con bên Quiz
    exercise_title: str | None = None       # Tiêu đề bài tập con
    submission_id: str | None = None        # UUID bản ghi nộp bài bên Quiz
    attempt_number: int = 1
    score: float | None = None
    original_filename: str | None = None
    
    # Chi tiết bổ sung (kết quả chấm test case, log, v.v.)
    details: dict[str, Any] = Field(default_factory=dict)
```

#### 2. Exercise Metadata Schema (`Quiz -> Manager`)
```python
class ExerciseItemDTO(BaseModel):
    id: str                                 # UUID bài tập con bên Quiz
    lesson_id: str
    title: str
    description: str = ""
    created_at: datetime
    has_attachment: bool = False
    order_index: int = 0


class LessonExercisesMetadataDTO(BaseModel):
    lesson_slug: str
    lesson_name: str
    total_exercises: int
    exercises: list[ExerciseItemDTO]
```

#### 3. Manager Detailed Status Response Schema (`Manager -> Frontend`)
```python
class ExerciseSubmissionDetailDTO(BaseModel):
    exercise_id: str
    exercise_title: str
    is_submitted: bool
    is_passed: bool = False
    score: float | None = None
    attempt_number: int = 0
    submitted_at: datetime | None = None
    is_late: bool = False


class StudentHomeworkProgressDTO(BaseModel):
    user_id: int
    user_name: str
    avatar_url: str | None = None
    total_required: int                     # Tổng số bài tập coding (N)
    total_completed: int                    # Số bài đã nộp thành công (k)
    is_fully_completed: bool                # k == N
    overall_is_late: bool                   # Có bài nào nộp trễ hoặc chưa nộp khi quá hạn
    exercises: list[ExerciseSubmissionDetailDTO]
```

---

### Key Entities

- **Bài học (`Lesson`)**: Thực thể bài học trên Quiz chứa `slug`, `name`, danh sách các bài tập coding con và ngân hàng câu hỏi game.
- **Bài tập coding con (`Exercise` / `HomeworkEntity` trong Quiz)**: Đại diện cho 1 bài tập lập trình cụ thể trong lesson với ID dạng UUID.
- **Lịch sử nộp bài chi tiết (`HomeworkSubmissionModel` trong Manager)**: Bản ghi bài nộp gắn liền với `homework_id`, `user_id`, và `exercise_id` (UUID từ Quiz), lưu vết điểm số, thời gian, lần nộp và file.
- **Trạng thái tiến độ học viên (`StudentHomeworkProgress`)**: Mô hình tổng hợp phản ánh mức độ hoàn thành ($k/N$ bài) của từng học viên được phân công.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: $100\%$ các bài nộp coding từ Quiz được Manager ghi nhận chính xác đến từng bài tập con (`exercise_id`), không xảy ra tình trạng ghi nhận hoàn thành cả lesson khi mới chỉ nộp $1/N$ bài.
- **SC-002**: Giao diện / API trạng thái nộp bài của Manager hiển thị đầy đủ danh sách $N$ bài tập con và tiến độ $k/N$ của từng học viên với thời gian phản hồi dưới $500\text{ ms}$.
- **SC-003**: Dữ liệu trao đổi qua Webhook và Sync API được xác thực $100\%$ bằng Pydantic Models, loại bỏ hoàn toàn các lỗi sai kiểu dữ liệu (Schema Mismatch).
- **SC-004**: Tác vụ quét quá hạn phát hiện chính xác $100\%$ các trường hợp học viên nộp thiếu bài tập con khi đã qua deadline.
- **SC-005**: Toàn bộ hệ thống test suite cho cả hai phía Quiz và Manager vượt qua $100\%$, Typecheck không có lỗi.

---

## Assumptions

- Mỗi bài tập coding trong một Lesson trên Quiz có một `id` duy nhất dạng UUID và không thay đổi trong suốt vòng đời của bài học.
- Học viên của hệ thống Manager có `user_id < 1,000,000` (được lọc tự động bên Quiz trước khi gửi webhook).
- Tiêu chuẩn hoàn thành phần Coding của một bài học là học viên phải nộp tất cả các bài tập coding đang kích hoạt (active) của bài học đó.
- Hệ thống duy trì tính tương thích ngược với các bản ghi lịch sử nộp bài cũ (những bản ghi chưa có `exercise_id` sẽ được gán giá trị mặc định hoặc null an toàn).
