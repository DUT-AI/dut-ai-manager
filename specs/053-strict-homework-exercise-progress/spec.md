# Feature Specification: Chuẩn hóa nghiêm ngặt tiến độ bài tập con và tách biệt Game Quiz

**Feature Branch**: `053-strict-homework-exercise-progress`  
**Created**: 2026-11-08  
**Status**: Draft  
**Input**: User description: "sửa lại giúp tôi lỗi này, đừng fall back gì có, hãy cố gắng nghiêm ngặt"

---

## Bối cảnh và Vấn đề (Context & Problem Statement)

1. **Thiếu bài tập con ở giao diện Học viên (User)**:
   - Một bài học có 2 bài tập coding con (ví dụ: *Bài tập đại số tuyến tính hơi cơ bản* và *Bài tập đại số tuyến tính*).
   - Khi học viên mới nộp 1 bài, trang chi tiết của học viên (`MyHomeworkDetailPage`) chỉ tải lịch sử nộp của chính mình mà không có danh mục bài tập con chính thức của bài học.
   - Hệ thống tự suy diễn số bài con dựa trên những bài đã nộp, dẫn đến bài chưa nộp biến mất hoàn toàn. Màn hình báo sai "Tiến độ 1/1 - Đã hoàn thành 100%" khiến học viên tưởng mình đã làm xong hết.

2. **Cơ chế Fallback lộn xộn ở Modal Admin**:
   - Ở modal chi tiết của Admin (`SubmissionHistoryModal`), hệ thống gom chung toàn bộ bài nộp (cả Coding và Game) vào một danh sách.
   - Do Game Quiz không có `exercise_id`, hệ thống tự động rơi vào fallback `__general__` và biến Game Quiz thành một bài tập con mang tên *"Bài tập chung"*.
   - Hậu quả: Tiến độ bài con bị đội lên thành `2/3 (67%)` dù bài học chỉ có 2 bài coding, gây mâu thuẫn trực tiếp với tiêu đề modal (`1/2 bài con`).

3. **Sai lệch hiển thị và ngộ nhận nghiệp vụ Game Quiz**:
   - **Thang điểm**: Game Quiz lưu điểm tích lũy/hệ số lớn (ví dụ: `89.0`), nhưng giao diện lại gán cứng mẫu số `/ 10` thành `89 / 10`.
   - **Tỷ lệ đúng**: Học viên đúng `6 / 10 câu`, nhưng giao diện lại gán cứng chuỗi `(100%)` thành `6 / 10 câu (100%)`.
   - **Nghiệp vụ Pass**: Nghiệp vụ thực tế của hệ thống là học viên hoàn thành phiên chơi game (`is_completed: true` trên Quiz API) là được tính `is_passed = True`, không phải bắt buộc đúng 100% số câu hỏi. Giao diện cần phản ánh đúng trạng thái `is_passed` này.

---

## User Scenarios & Testing *(Bắt buộc)*

### User Story 1 - Học viên xem đầy đủ danh mục bài tập con kể cả bài chưa nộp (Priority: P1)

Là một học viên đang học tập, tôi muốn xem chính xác tất cả các bài tập coding con của bài học cùng trạng thái thực tế (đã nộp hay chưa nộp), để tôi biết mình còn bài nào chưa làm và không bị lầm tưởng là đã hoàn thành 100%.

**Why this priority**: Đây là lỗi nghiêm trọng ảnh hưởng trực tiếp đến kết quả học tập của sinh viên. Nếu sinh viên tưởng đã nộp đủ thì sẽ bị quá hạn bài tập.

**Independent Test**:
- Học viên truy cập bài tập có 2 bài coding con, trong đó học viên mới chỉ nộp 1 bài.
- Giao diện phải hiển thị rõ ràng:
  - Tiến độ: `1/2 bài tập con (50% hoàn thành)`.
  - Bài 1: Đã nộp (kèm điểm số và số lần nộp).
  - Bài 2: Chưa nộp (0 lần nộp, kèm nút/link để làm bài).
  - Không được phép hiển thị 1/1 hay 100% khi còn bài con chưa nộp.

**Acceptance Scenarios**:
1. **Given** một bài tập có $N$ bài coding con ($N \ge 1$), **When** học viên vào trang chi tiết bài tập của tôi (`MyHomeworkDetailPage`), **Then** hệ thống hiển thị danh sách đầy đủ $N$ bài con từ danh mục chính thức, không phụ thuộc vào việc học viên đã nộp hay chưa.
2. **Given** học viên chưa nộp bất kỳ bài coding nào ($0/N$), **When** học viên vào trang, **Then** hệ thống hiển thị đầy đủ $N$ bài con ở trạng thái "Chưa nộp" kèm hướng dẫn nộp bài, không hiển thị màn hình trống trơn.
3. **Given** học viên đã nộp đủ $N/N$ bài con, **When** học viên kiểm tra, **Then** thanh tiến độ mới hiển thị $N/N$ và trạng thái "Đã hoàn thành tất cả bài tập Coding".

---

### User Story 2 - Loại bỏ fallback "Bài tập chung", tách biệt rõ ràng Coding và Game ở Admin (Priority: P2)

Là một Quản trị viên/Giảng viên, khi xem lịch sử nộp bài của một học viên, tôi muốn cấu trúc bài tập hiển thị nghiêm ngặt đúng số lượng bài coding thực tế, không bị Game Quiz trà trộn vào danh sách bài con dưới nhãn fallback "Bài tập chung".

**Why this priority**: Giúp Admin đánh giá chính xác học viên làm được bao nhiêu bài coding con mà không bị sai lệch số liệu (tránh mâu thuẫn giữa header 1/2 và thân modal 2/3).

**Independent Test**:
- Mở modal lịch sử nộp bài của học viên Đỗ Quảng Giác ở bài tập "Gen2: Đại số tuyến tính".
- Tiến độ bài con phải hiển thị chính xác `1/2 bài con` (chỉ gồm 2 bài coding).
- Game Quiz phải được tách riêng thành mục hoặc tab riêng, không nằm chung trong thanh bài tập coding con và không tạo ra nhãn "Bài tập chung".

**Acceptance Scenarios**:
1. **Given** học viên có cả bài nộp Coding và bài nộp Game Quiz, **When** Admin mở `SubmissionHistoryModal`, **Then** danh sách bài tập coding con chỉ chứa đúng các bài tập coding từ cấu trúc bài học (không xuất hiện "Bài tập chung").
2. **Given** bài nộp Game Quiz không có `exercise_id`, **When** render tiến độ bài tập con Coding, **Then** hệ thống loại trừ các bản ghi Game Quiz ra khỏi danh sách bài tập coding con một cách nghiêm ngặt.
3. **Given** modal Admin hiển thị số lượng bài con, **When** đối chiếu giữa tiêu đề modal và thân modal, **Then** số lượng bài con hoàn thành/tổng số bài con phải khớp nhau 100% (ví dụ: cùng là 1/2).

---

### User Story 3 - Hiển thị chuẩn xác số liệu và trạng thái của Game Quiz (Priority: P3)

Là một học viên hoặc quản trị viên, tôi muốn nhìn thấy kết quả Game Quiz với số điểm thực tế, số câu đúng thực tế và trạng thái đạt chuẩn xác, không bị gán cứng text sai lệch.

**Why this priority**: Đảm bảo tính minh bạch, nhất quán và tránh gây hiểu lầm cho người dùng về quy chế hoàn thành Game.

**Independent Test**:
- Kiểm tra thẻ bài nộp Game Quiz của học viên có 6/10 câu đúng, điểm 89.
- Điểm số phải hiển thị là `89 điểm` (hoặc `89` không có `/ 10` nếu thang điểm không phải 10).
- Số câu đúng hiển thị là `6 / 10 câu` (kèm tỷ lệ chính xác `60%`, tuyệt đối không hardcode `(100%)`).
- Trạng thái hoàn thành được xác định theo `is_passed` (đã hoàn thành phiên chơi game).

**Acceptance Scenarios**:
1. **Given** một bản ghi Game Quiz có `correct_count = 6` và `total_questions = 10`, **When** hiển thị thẻ kết quả, **Then** hệ thống tính tỷ lệ phần trăm đúng theo công thức thực tế $\frac{\text{correct\_count}}{\text{total\_questions}} \times 100\% = 60\%$, không gõ cứng `(100%)`.
2. **Given** điểm Game Quiz lưu dạng số thực (ví dụ 89.0), **When** hiển thị điểm, **Then** hệ thống hiển thị điểm rõ ràng kèm đơn vị điểm phù hợp, không ép buộc chia cho 10 khi không thuộc thang điểm 10.
3. **Given** banner quy định hoàn thành, **When** bài tập yêu cầu Game, **Then** nội dung mô tả nêu rõ: "Hoàn thành phiên Game trắc nghiệm" thay vì text gõ cứng "đúng 100%".

---

### Edge Cases

- **Bài học không có bài tập coding nào** (`requires_coding = false`): Hệ thống chỉ hiển thị tab/mục Game Quiz, không render thanh tiến độ bài tập coding con.
- **Bài học chưa có dữ liệu cấu trúc bài tập con** (ví dụ Quiz API chưa có dữ liệu và chưa có ai nộp bài): Hệ thống hiển thị rõ thông báo "Chưa có danh mục bài tập con" thay vì tự tạo nhóm ảo.
- **Học viên nộp nhiều lần cho cùng 1 bài coding con**: Hệ thống hiển thị số lần nộp (attempt count), lấy điểm cao nhất và lần nộp gần nhất theo đúng quy tắc, không nhân đôi bài tập con.
- **Bản ghi nộp bài không xác định được loại**: Hệ thống phân loại chặt chẽ dựa trên trường `submission_type` (chỉ chấp nhận `CODING` hoặc `GAME`), từ chối phân loại mơ hồ.

---

## Requirements *(Bắt buộc)*

### Functional Requirements

- **FR-001 (Backend Contract)**: API lấy thông tin chi tiết bài tập (`GET /homeworks/{homework_id}`) MUST trả về danh mục chính thức các bài tập coding con (`coding_exercises: list[ExerciseSummaryDTO]`), gồm `exercise_id`, `title`, `order_index`.
- **FR-002 (Single Source of Truth)**: Danh mục `coding_exercises` phải là nguồn chân lý duy nhất (Single Source of Truth) để tính toán số lượng và tiến độ bài tập con của bài học, cấm frontend tự đếm số lượng bài con từ mảng bài đã nộp.
- **FR-003 (Frontend My Homework Detail)**: Component `MyHomeworkDetailPage` MUST truyền danh mục bài tập con chính thức `coding_exercises` vào component hiển thị tiến độ bài tập coding, đảm bảo tất cả bài tập con (kể cả bài chưa nộp) đều được hiển thị đầy đủ.
- **FR-004 (Strict Exercise Grouping)**: Hàm `groupSubmissionsByExercise` MUST chỉ gom nhóm các bài nộp có `submission_type === 'CODING'`. Cấm đưa các bài nộp không phải Coding hoặc bài nộp Game vào danh sách bài tập con dưới nhãn fallback `__general__` / "Bài tập chung".
- **FR-005 (Admin Modal Consistency)**: Modal `SubmissionHistoryModal` MUST lọc rõ ràng các bài nộp:
  - Khi hiển thị tiến độ Coding: chỉ truyền danh sách bài nộp Coding và danh mục `coding_exercises`.
  - Khi có Game Quiz: hiển thị riêng biệt theo tab hoặc section độc lập cho Game, không gộp chung vào timeline Coding.
- **FR-006 (Game Score Rendering)**: Thẻ hiển thị bài nộp `SubmissionItemCard` MUST phân biệt cách hiển thị điểm giữa Coding và Game:
  - Với Coding (chấm thang 10): hiển thị `{score} / 10`.
  - Với Game (điểm game/tích lũy): hiển thị `{score} điểm` (không kèm `/ 10`).
- **FR-007 (Game Correct Rate Dynamic Calculation)**: Thẻ `SubmissionItemCard` MUST tính tỷ lệ câu đúng bằng công thức động: `Math.round((correct_count / total_questions) * 100)%`. Tuyệt đối cấm gán cứng chuỗi `(100%)`.
- **FR-008 (Text & Status Alignment)**: Loại bỏ toàn bộ các text gõ cứng "đúng 100%" ở banner quy định, tab Game và tiêu đề, thay bằng mô tả đúng chuẩn nghiệp vụ: "Hoàn thành bài tập Game trắc nghiệm". Trạng thái hoàn thành Game được xác định dựa trên trường `is_passed` của bài nộp.

### Key Entities

- **Homework**: Bài tập lớn được giao, chứa các thuộc tính: `id`, `title`, `deadline`, `requires_coding`, `requires_game`, `slug`, và danh mục `coding_exercises`.
- **ExerciseSummary**: Thông tin một bài tập coding con thuộc bài học: `exercise_id`, `title`, `order_index`.
- **HomeworkSubmission**: Bản ghi nộp bài của học viên, gồm: `id`, `homework_id`, `user_id`, `submission_type` (`CODING` | `GAME`), `exercise_id` (chỉ có ở Coding), `score`, `is_passed`, `details` (chứa `correct_count`, `total_questions`, `final_score` cho Game).

---

## Success Criteria *(Bắt buộc)*

### Measurable Outcomes

- **SC-001 (Đầy đủ bài con 100%)**: Ở màn hình học viên, 100% các bài học có bài coding con đều hiển thị đúng tổng số bài con của đề bài, không còn tình trạng bài chưa nộp bị biến mất.
- **SC-002 (Không còn "Bài tập chung" ảo)**: Ở cả giao diện Admin và User, tỷ lệ xuất hiện nhóm fallback "Bài tập chung" trong danh sách bài coding con giảm về 0%.
- **SC-003 (Đồng nhất số liệu Admin Modal)**: Số lượng bài con trên tiêu đề modal (`X/Y bài con`) và thanh tiến độ trong thân modal (`X/Y bài con`) đạt độ nhất quán 100%.
- **SC-004 (Độ chính xác hiển thị Game)**: 100% các bản ghi Game Quiz hiển thị đúng thang điểm và đúng tỷ lệ câu đúng thực tế, không còn xuất hiện lỗi `89 / 10` hay `6 / 10 câu (100%)`.

---

## Assumptions

- Danh mục bài tập coding con của một bài học được lấy từ Quiz API thông qua `slug`, hoặc nếu Quiz API chưa khả dụng thì lấy từ danh mục bài tập con đã được cấu hình/ghi nhận chuẩn trong bài học.
- Tiêu chuẩn đạt của Game Quiz theo quy định của hệ thống là học viên hoàn thành phiên chơi (`is_completed = true` tương đương `is_passed = True`).
- Các bài tập coding con sử dụng thang điểm chuẩn 10, trong khi Game Quiz có thể có điểm tích lũy theo thang điểm riêng.
