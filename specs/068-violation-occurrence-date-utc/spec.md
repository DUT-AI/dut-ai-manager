# Feature Specification: Chuẩn Hóa Thời Gian Xảy Ra Vi Phạm Tự Động Theo UTC

**Feature Branch**: `068-violation-occurrence-date-utc`

**Created**: 2026-11-13

**Status**: Draft

**Input**: User description: "Tôi muốn chỉnh sửa lại các job tạo vi phạm tự động, date sẽ là giờ xảy ra vi phạm, không phải là giờ tạo vi phạm => UTC để client có xem được múi h tương ứng của họ trên ui"

## Clarifications

### Session 2026-11-13
- Q: Hệ thống có cần chạy migration / script để cập nhật hồi cứu (backfill) trường `date` cho các vi phạm tự động đã tạo trước đây trong cơ sở dữ liệu không? → A: Chỉ áp dụng logic mới cho các vi phạm được tạo ra từ thời điểm triển khai trở đi (giữ nguyên dữ liệu cũ).
- Q: Đối với bộ lọc thời gian khi xem danh sách vi phạm (`/api/v1/violations?start_date=...&end_date=...`), API nên tiếp tục lọc theo trường `date` (ngày xảy ra vi phạm) hay cung cấp thêm bộ lọc theo `created_at` (ngày tạo vi phạm trên hệ thống)? → A: Giữ nguyên lọc theo `date` (thời điểm xảy ra vi phạm) như hiện tại.
- Q: Khi so sánh và phát hiện vi phạm trùng lặp trong `CreateViolationUseCase` (`is_system=True`), nếu job chạy quét lại cùng một vi phạm, hệ thống nên kiểm tra sự tồn tại dựa trên tiêu chí nào? → A: Giữ nguyên logic kiểm tra trong cùng ngày (`target_date.date()`) kết hợp so khớp lý do (`v.reason == reason`).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Vi phạm Vắng sinh hoạt & Đi trễ ghi nhận chính xác thời gian xảy ra (Priority: P1)

Với tư cách là thành viên câu lạc bộ hoặc quản trị viên, tôi muốn khi bị ghi nhận vi phạm vắng sinh hoạt hoặc đi trễ (do job điểm danh hoặc sự kiện điểm danh kích hoạt), trường `date` của vi phạm phải phản ánh chính xác thời gian bắt đầu buổi họp (với vắng họp) hoặc thời gian quẹt thẻ check-in thực tế (với đi trễ) dưới định dạng timezone-aware UTC, thay vì thời điểm 23:59 đêm khi background job chạy.

**Why this priority**: Đảm bảo tính công bằng và minh bạch lịch sử. Khi xem trên giao diện web/mobile, thành viên nhìn thấy vi phạm gắn đúng với giờ diễn ra buổi sinh hoạt tại múi giờ địa phương của họ (ví dụ: 18:00 UTC+7 tương ứng 11:00 UTC) thay vì thời điểm nửa đêm hệ thống quét dữ liệu.

**Independent Test**: Kích hoạt `CheckMeetingAttendanceUseCase` cho một buổi họp kết thúc lúc 19:30 ngày hôm trước (start lúc 18:00 UTC+7). Kiểm tra vi phạm vắng mặt tạo ra có trường `date` bằng `meeting.start_time` (chuẩn hóa UTC), và vi phạm đi trễ có trường `date` bằng `participant.check_in_at` (chuẩn hóa UTC).

**Acceptance Scenarios**:

1. **Given** một buổi họp có `start_time` lúc 18:00 (UTC+7), học viên A không check-in, **When** job kiểm tra điểm danh chạy lúc 23:59 (hoặc trễ 2 ngày), **Then** vi phạm vắng mặt được tạo với `date` chính là `meeting.start_time` (chuẩn hóa UTC).
2. **Given** học viên B check-in lúc 18:15 (trễ quá giờ quy định), **When** sự kiện đi trễ được xử lý, **Then** vi phạm đi trễ được tạo với `date` chính là `check_in_at` (18:15 UTC+7 chuyển sang UTC).

---

### User Story 2 - Vi phạm Trực nhật & Quá hạn bài tập & Đánh giá buổi học ghi nhận đúng mốc hạn (Priority: P2)

Với tư cách là học viên, tôi muốn khi bị ghi nhận vi phạm không làm trực nhật, nộp bài tập muộn hoặc quên đánh giá buổi học, trường `date` của vi phạm ghi nhận chính xác thời điểm xảy ra vi phạm:
- Với trực nhật: thời điểm kết thúc buổi học liên quan hoặc thời điểm cuối ngày trực nhật (23:59:59 UTC+7 chuyển sang UTC).
- Với bài tập: thời điểm hạn chót (`deadline`) của chính học viên đó (đã bao gồm gia hạn nếu có) dưới dạng UTC.
- Với đánh giá buổi học: thời điểm kết thúc 24h kể từ khi buổi học kết thúc (`meeting.end_time + 24h` chuẩn UTC) hoặc thời điểm `meeting.end_time`.

**Why this priority**: Loại bỏ hoàn toàn sự sai lệch giữa "ngày tạo vi phạm trên hệ thống" và "thời điểm xảy ra sự việc vi phạm".

**Independent Test**: Chạy `CheckOverdueHomeworkUseCase` với bài tập có deadline là 23:59:00 ngày D. Vi phạm tạo ra phải có trường `date` trùng khớp với `assignment.deadline` (UTC).

**Acceptance Scenarios**:

1. **Given** bài tập có hạn nộp là `2026-11-10 16:59:59 UTC` (tức 23:59:59 UTC+7), học viên chưa nộp, **When** job quét bài tập quá hạn kích hoạt sau đó 2 ngày, **Then** vi phạm được tạo có trường `date` bằng chính xác deadline `2026-11-10 16:59:59 UTC`.
2. **Given** ca trực nhật ngày D gắn với buổi họp kết thúc lúc 11:30 UTC, học viên trong nhóm không hoàn thành, **When** job kiểm tra trực nhật kích hoạt, **Then** vi phạm có trường `date` được gán theo thời gian buổi trực nhật/hạn trực nhật.
3. **Given** buổi học kết thúc lúc `2026-11-10 10:00:00 UTC`, sau 24h (`2026-11-11 10:00:00 UTC`) trainer chưa đánh giá, **When** job quét đánh giá kích hoạt, **Then** vi phạm được tạo có trường `date` là `meeting.end_time + 24h` (thời điểm chính thức hết hạn).

---

### User Story 3 - Hiển thị đúng múi giờ địa phương trên UI (Priority: P3)

Với tư cách là người dùng ở bất kỳ múi giờ nào (mặc định Việt Nam UTC+7), tôi muốn giao diện hiển thị giờ vi phạm tương ứng với múi giờ của trình duyệt/thiết bị từ chuỗi UTC ISO 8601 mà backend cung cấp.

**Why this priority**: Đảm bảo dữ liệu gửi từ backend dưới dạng timezone-aware UTC được parse và hiển thị tự nhiên bằng Dayjs/Intl ở frontend mà không bị lệch ngày hay lệch giờ.

**Independent Test**: Gửi request API lấy danh sách vi phạm, kiểm tra trường `date` trả về kết thúc bằng `Z` hoặc `+00:00`, và trên component `ViolationTable` hiển thị chính xác theo local time của client.

**Acceptance Scenarios**:

1. **Given** vi phạm có `date` lưu trong DB là `2026-11-10 11:00:00+00:00`, **When** API trả về DTO `2026-11-10T11:00:00Z`, **Then** giao diện `ViolationTable` hiển thị `10/11/2026 18:00` (đối với client UTC+7).

---

## Edge Cases

- **Meeting/Homework thiếu thông tin start_time hoặc deadline**: Fallback an toàn về `datetime.now(UTC)` nếu thực thể thiếu mốc thời gian sự kiện.
- **Start_time / deadline là naive datetime (không có tzinfo)**: Phải được chuẩn hóa ép kiểu về timezone-aware (nếu naive, mặc định gán UTC hoặc interpret Asia/Ho_Chi_Minh trước khi chuyển UTC theo Principle III Constitution).
- **Trùng lặp vi phạm khi job quét nhiều lần**: Hàm kiểm tra vi phạm trùng lặp `get_by_user_and_date` hoặc `exists_by_user_and_reason` tiếp tục so sánh theo ngày của `date` (`target_date.date()`) kết hợp so khớp lý do `v.reason == reason`. Do `date` giờ đây là mốc thời gian cố định của sự việc (thay vì thời gian job chạy), việc kiểm tra này đảm bảo tính lũy thừa (idempotency) hoàn hảo.
- **Dữ liệu lịch sử cũ**: Không chạy backfill hồi cứu, dữ liệu vi phạm cũ giữ nguyên giá trị `date` ban đầu.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Toàn bộ vi phạm tự động sinh ra từ background jobs / domain event handlers PHẢI gán trường `date` là thời gian xảy ra sự kiện vi phạm (occurrence timestamp), được chuẩn hóa thành timezone-aware UTC.
- **FR-002**: Vi phạm vắng sinh hoạt (`_handle_meeting_absence`) PHẢI nhận mốc thời gian là thời gian bắt đầu của buổi họp (`meeting.start_time`).
- **FR-003**: Vi phạm đi trễ sinh hoạt (`_handle_meeting_late`) PHẢI nhận mốc thời gian là thời gian quẹt thẻ check-in thực tế của thành viên (`event.check_in_at`).
- **FR-004**: Vi phạm quá hạn bài tập (`_handle_homework_overdue` / `HomeworkOverdueDetected`) PHẢI nhận mốc thời gian là `assignment.deadline` (chuẩn hóa UTC).
- **FR-005**: Vi phạm trực nhật quá hạn (`CheckOverdueDutiesUseCase`) PHẢI nhận mốc thời gian là thời điểm kết thúc buổi học (`meeting.end_time`) nếu ca trực theo meeting, hoặc mốc 23:59:59 của ngày trực nhật theo giờ Việt Nam chuyển đổi sang UTC nếu ca trực tự do.
- **FR-006**: Vi phạm quá hạn đánh giá 24h buổi học (`CheckEvaluationDeadlineJobUseCase`) PHẢI nhận mốc thời gian là `meeting.end_time + timedelta(hours=24)` (thời điểm chính thức vi phạm hạn 24h).
- **FR-007**: Domain Events (`ParticipantAbsenceRecorded`, `ParticipantLateRecorded`, `HomeworkOverdueDetected`) PHẢI truyền tải đầy đủ thuộc tính datetime của sự kiện (thay vì chỉ truyền date string hoặc bỏ sót timestamp).
- **FR-008**: API backend trả về trường `date` của `Violation` ở chuẩn ISO 8601 UTC và frontend hiển thị theo local timezone của người dùng.
- **FR-009**: Hệ thống KHÔNG thực hiện thay đổi dữ liệu hồi cứu (backfill) đối với các vi phạm đã tạo trong quá khứ; quy tắc mới chỉ áp dụng cho các vi phạm tạo ra sau thời điểm triển khai.
- **FR-010**: Bộ lọc danh sách vi phạm (`/api/v1/violations?start_date=...&end_date=...`) PHẢI tiếp tục truy vấn và lọc theo trường `date` (thời điểm xảy ra vi phạm) theo khoảng ngày được chỉ định.
- **FR-011**: Cơ chế chống trùng lặp hệ thống (`CreateViolationUseCase` khi `is_system=True`) PHẢI kiểm tra các vi phạm trong cùng ngày của sự kiện (`date.date()`) và so sánh `v.reason == reason` để ngăn việc tạo trùng khi job quét lại.

### Key Entities

- **Violation**: Thực thể vi phạm với `date` (datetime, timezone-aware UTC) đại diện cho thời điểm xảy ra hành vi vi phạm.
- **ParticipantAbsenceRecorded**: Sự kiện vắng họp, bổ sung thuộc tính `start_time: datetime | None`.
- **HomeworkOverdueDetected**: Sự kiện bài tập quá hạn, bổ sung thuộc tính `deadline: datetime`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% các vi phạm tự động tạo ra từ jobs có `date` trùng khớp với thời điểm xảy ra sự việc (start_time buổi họp, check_in_at, deadline bài tập, deadline 24h đánh giá, thời gian ca trực).
- **SC-002**: Tất cả giá trị `date` lưu vào DB và trả ra API đều là timezone-aware UTC (`+00:00` / `Z`).
- **SC-003**: Kiểm thử tự động (Unit test / Integration test) của tất cả các use case và job liên quan chạy pass 100%.

## Assumptions

- Múi giờ mặc định của các sự kiện diễn ra tại Việt Nam là `Asia/Ho_Chi_Minh` nếu mốc thời gian đầu vào là naive datetime.
- Frontend đã sử dụng `dayjs(date).format(...)` tự động parse UTC string sang local timezone của client.
