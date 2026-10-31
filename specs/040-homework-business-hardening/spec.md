# Feature Specification: Củng Cố Toàn Diện Nghiệp Vụ Bài Tập (Homework Business Hardening)

**Feature Branch**: `040-homework-business-hardening`

**Created**: 2026-10-31

**Status**: Draft

**Input**: User description: "1. Scanner nhắc nhở bài tập bỏ sót học sinh chưa hoàn thành đủ bài. 2. Suy đoán mò mẫm danh sách bài tập con qua lịch sử nộp bài cũ. 3. Các kịch bản lách luật khi tạo đơn xin hoãn bài tập (PostponeStrategy) => cho phép xin hoãn nhiều lần tích lũy nhé, vì theo quy định trong 1 tháng nếu hoãn nhiều lần sẽ bị auto tạo vi phạm rồi."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Nhắc nhở bài tập chính xác cho học sinh chưa hoàn thành đủ bài (Priority: P1)

Là một học viên được giao bài tập (có yêu cầu cả Coding và Game, hoặc bài Coding có nhiều bài con), tôi muốn nhận được thông báo nhắc nhở tự động trước hạn nộp nếu tôi chưa hoàn thành đầy đủ tất cả các yêu cầu của bài tập, để tôi kịp thời nộp đủ bài và không bị phạt vi phạm quá hạn.

**Why this priority**: Hiện tại hệ thống nhắc nhở chỉ kiểm tra sơ sài sự tồn tại của bất kỳ bản ghi nộp bài nào (`if submissions: continue`). Nếu học sinh mới chỉ làm Game hoặc mới nộp 1 bài con Coding thì hệ thống đã bỏ qua không nhắc nhở, dẫn đến học sinh vô tình bị phạt oan do quên làm phần còn lại.

**Independent Test**: Giao bài tập yêu cầu cả Coding và Game. Học sinh chỉ nộp Game. Kích hoạt scanner nhắc nhở: hệ thống phải nhận diện học sinh chưa hoàn thành Coding và gửi thông báo nhắc nhở chính xác.

**Acceptance Scenarios**:

1. **Given** một bài tập yêu cầu cả Coding và Game, **When** học sinh chỉ mới hoàn thành Game mà chưa hoàn thành Coding, **Then** hệ thống nhắc nhở phải đánh giá trạng thái là chưa hoàn thành (`is_submitted == False`) và gửi thông báo nhắc nhở trước deadline cá nhân của học sinh.
2. **Given** một bài tập Coding có 3 bài con, **When** học sinh mới chỉ nộp 1 bài hoặc nộp bài bị chấm trượt (`is_passed == False`), **Then** hệ thống nhắc nhở vẫn tiếp tục gửi thông báo nhắc nhở cho học sinh.
3. **Given** học sinh đã hoàn thành đầy đủ cả Coding (tất cả bài con đều pass) và Game trước hạn, **When** scanner chạy, **Then** học sinh đó được bỏ qua và không nhận thông báo nhắc nhở dư thừa.

---

### User Story 2 - Quản lý và đối soát bài tập con từ nguồn Quiz API chuẩn xác (Priority: P2)

Là một Quản trị viên (Admin/Trainer) hoặc Hệ thống tự động quét quá hạn, tôi muốn danh sách bài tập con của từng bài học luôn được lấy từ nguồn chính thống của Quiz API, để bảng tiến độ nộp bài hiển thị đầy đủ ngay cả khi chưa ai nộp, và việc tính toán hoàn thành bài tập không bị sai lệch khi lớp có ít bài nộp.

**Why this priority**: Hiện tại hệ thống tự suy diễn danh sách bài con từ các bài nộp cũ trong database. Nếu bài mới giao chưa ai nộp thì hiển thị 0 bài con; nếu chỉ mới 1 người nộp 1 bài con thì người khác chỉ cần nộp đúng bài con đó là hệ thống tưởng đã hoàn thành toàn bộ bài tập.

**Independent Test**: Tạo một bài tập Coding mới trên hệ thống chưa có ai nộp bài. Truy cập màn hình chi tiết bài tập: hệ thống phải hiển thị đầy đủ danh sách các bài tập con lấy từ Quiz API. Khi một học sinh chỉ nộp 1 trong 3 bài con, hệ thống phải xác định chính xác là chưa hoàn thành (chưa đủ các bài con còn lại).

**Acceptance Scenarios**:

1. **Given** một bài tập Coding mới được giao và chưa có học sinh nào nộp bài, **When** Admin xem màn hình chi tiết hoặc API báo cáo nộp bài (`GetHomeworkSubmissionStatusUseCase`), **Then** danh mục các bài tập con (`coding_exercises`) hiển thị đầy đủ dựa trên dữ liệu từ Quiz API.
2. **Given** bài tập trên Quiz có các bài tập con A, B, C, **When** tiến trình quét quá hạn (`CheckOverdueHomeworkUseCase`) chạy, **Then** hệ thống yêu cầu học sinh phải hoàn thành đầy đủ tập hợp các bài tập con {A, B, C} mới được coi là hoàn thành Coding.
3. **Given** trường hợp dịch vụ Quiz API tạm thời không phản hồi hoặc mất kết nối, **When** use case thực thi, **Then** hệ thống sử dụng cơ chế fallback thông minh (tổng hợp từ các bài nộp đã ghi nhận trước đó) để đảm bảo tính sẵn sàng cao mà không làm sập tiến trình.

---

### User Story 3 - Kiểm soát chặt chẽ tính hợp lệ của đơn xin hoãn bài tập (Priority: P3)

Là một Học sinh hoặc Quản trị viên, tôi muốn quy trình tạo đơn xin hoãn bài tập tuân thủ đúng quy định (chỉ được xin hoãn khi bài tập chưa quá hạn, thời gian gia hạn phải ở tương lai, không cho phép hoãn bài đã làm xong, và cho phép hoãn tích lũy theo từng lần tối đa 4 ngày), để đảm bảo tính công bằng và kỷ luật của trung tâm.

**Why this priority**: Khắc phục các kịch bản lách luật như tạo đơn hoãn lùi về quá khứ sau khi đã bị phạt vi phạm, hoặc tạo đơn hoãn cho bài tập mình đã nộp xong. Đồng thời hỗ trợ nghiệp vụ hoãn tích lũy (cho phép hoãn nhiều lần nối tiếp nhau nếu học sinh tiếp tục gặp khó khăn, vì hệ thống tự động đã có cơ chế tính vi phạm nếu hoãn quá số lần quy định trong tháng).

**Independent Test**: Thử tạo đơn hoãn với ngày gia hạn trong quá khứ -> hệ thống từ chối. Thử tạo đơn hoãn cho bài tập đã nộp hoàn thành -> hệ thống từ chối. Thử tạo đơn hoãn khi deadline bài tập đã qua -> hệ thống từ chối. Thử tạo đơn hoãn lần 2 sau khi lần 1 đã dời deadline -> hệ thống cho phép gia hạn tiếp nếu <= 4 ngày so với deadline hiện tại.

**Acceptance Scenarios**:

1. **Given** học sinh có bài tập chưa nộp và hạn nộp hiện tại vẫn còn hiệu lực (`current_deadline > now`), **When** học sinh xin hoãn với mốc thời gian mới trong tương lai và cách hạn nộp hiện tại không quá 4 ngày, **Then** hệ thống chấp thuận và cập nhật deadline mới của học sinh.
2. **Given** bài tập của học sinh đã quá hạn tại thời điểm tạo đơn (`current_deadline <= now`), **When** học sinh gửi đơn xin hoãn, **Then** hệ thống từ chối với thông báo "Bài tập đã quá hạn, không thể tạo đơn xin hoãn".
3. **Given** thời gian xin gia hạn được chọn nằm ở quá khứ (`extended_deadline <= now`), **When** học sinh gửi đơn, **Then** hệ thống từ chối với thông báo "Thời gian gia hạn mới phải ở tương lai".
4. **Given** học sinh đã nộp đủ và hoàn thành bài tập (`is_submitted == True`), **When** học sinh gửi đơn xin hoãn bài tập đó, **Then** hệ thống từ chối với thông báo "Bạn đã hoàn thành bài tập này, không thể xin hoãn".
5. **Given** học sinh đã xin hoãn lần 1 thành công (deadline dời từ ngày 5 sang ngày 9), **When** vào ngày 8 học sinh tiếp tục xin hoãn đến ngày 12 (cách hạn hiện tại 3 ngày), **Then** hệ thống chấp thuận tạo đơn xin hoãn tích lũy lần 2 theo đúng quy chế.

---

### Edge Cases

- **Khi Quiz API trả về danh sách bài tập rỗng hoặc bị lỗi mạng**: Hệ thống tự động fallback sử dụng danh sách `exercise_id` đã từng được ghi nhận trong `homework_submissions`, ghi log cảnh báo và không làm gián đoạn tiến trình.
- **Khi một bài tập có bài con bị xoá hoặc đổi slug trên Quiz**: Hệ thống so sánh theo `exercise_id` chuẩn hóa dạng chuỗi để tránh lệch kiểu giữa số nguyên và chuỗi.
- **Học sinh xin hoãn sát giờ (còn 1 phút trước hạn nộp)**: Hệ thống sử dụng thời gian UTC chuẩn hóa để kiểm tra `current_deadline > now`, bảo đảm không bị lệch múi giờ giữa client và server.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống nhắc nhở (`HomeworkTaskScanner`) BẮT BUỘC sử dụng phương thức đánh giá nghiệp vụ tổng thể `Homework.evaluate_submissions()` thay vì chỉ kiểm tra sự tồn tại của mảng bài nộp, bảo đảm học sinh chưa hoàn thành trọn vẹn cả Coding và Game sẽ tiếp tục nhận được nhắc nhở.
- **FR-002**: Hệ thống BẮT BUỘC tích hợp lấy danh mục bài tập con chính thức từ `QuizApiClient.get_lesson_exercises(slug)` trong các use case theo dõi tiến độ (`GetHomeworkSubmissionStatusUseCase`) và quét quá hạn (`CheckOverdueHomeworkUseCase`).
- **FR-003**: Hệ thống BẮT BUỘC duy trì cơ chế Fallback an toàn khi Quiz API không phản hồi hoặc trả về lỗi, đảm bảo các nghiệp vụ cốt lõi không bị tê liệt.
- **FR-004**: Đơn xin hoãn nộp bài (`PostponeStrategy`) BẮT BUỘC từ chối nếu:
  - Thời gian gia hạn mới ở trong quá khứ so với thời điểm gửi đơn (`extended_deadline <= now`).
  - Hạn nộp hiện tại của học sinh đã hết hạn tại thời điểm gửi đơn (`current_deadline <= now`).
  - Học sinh đã hoàn thành đầy đủ bài tập đó (`hw.evaluate_submissions().is_submitted == True`).
- **FR-005**: Đơn xin hoãn nộp bài BẮT BUỘC cho phép hoãn tích luỹ nhiều lần, mỗi lần cách hạn nộp hiện tại không quá 4 ngày (`0 < extended_deadline - current_deadline <= 4 ngày`).

### Key Entities

- **Homework**: Đại diện cho bài tập, chứa các quy tắc nghiệp vụ đánh giá bài nộp (`evaluate_submissions`), phân loại Coding và Game.
- **HomeworkAssignee**: Mối quan hệ giao bài giữa bài tập và từng học sinh, lưu trữ hạn nộp hiệu lực cá nhân (`deadline`).
- **HomeworkSubmission**: Bản ghi lịch sử nộp bài của học sinh (Coding con hoặc Game trắc nghiệm).
- **PostponePayload**: Dữ liệu chi tiết của đơn xin hoãn nộp bài (`homework_id`, `start_time` - thời gian gia hạn, `old_deadline` - hạn cũ để khôi phục khi hủy).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% học sinh chưa hoàn thành đủ bài tập (thiếu Coding hoặc thiếu Game) nhận được thông báo nhắc nhở tự động trước hạn nộp cá nhân.
- **SC-002**: 100% bài tập mới tạo hiển thị chính xác danh mục bài tập con ngay cả khi chưa có lượt nộp bài nào trong cơ sở dữ liệu.
- **SC-003**: 0 trường hợp học sinh tạo được đơn xin hoãn lùi về quá khứ hoặc xin hoãn sau khi bài tập đã quá hạn nộp.
- **SC-004**: Toàn bộ hệ thống kiểm thử tự động (Unit, Integration, API tests) đạt tỷ lệ vượt qua 100% không có hồi quy (Zero Regression).

## Assumptions

- Quiz API cung cấp endpoint `/api/v1/lessons/{lesson_slug}/exercises` trả về danh sách các bài tập con có cấu trúc `id`, `title`.
- Chính sách vi phạm của trung tâm đã có cơ chế tự động đếm số lần xin hoãn trong tháng để phát hiện lạm dụng, do đó việc cho phép hoãn tích lũy từng đợt <= 4 ngày là hoàn toàn phù hợp và an toàn.
