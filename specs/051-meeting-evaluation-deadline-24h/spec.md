# Feature Specification: Điều Chỉnh Thời Hạn Đánh Giá Cuộc Họp Từ 72 Giờ Về 24 Giờ (Meeting Evaluation Deadline 24 Hours)

**Feature Branch**: `051-meeting-evaluation-deadline-24h`

**Created**: 2026-11-05

**Status**: Draft

**Input**: User description: "Hiện tại tôi muốn bỏ đi nghiệp vụ quá 72h chưa đánh giá là bị phạt, chỉ cần quá 24h là được"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tự động ghi nhận vi phạm khi quá 24 giờ chưa đánh giá cuộc họp (Priority: P1) 🎯 MVP

Là Quản trị viên hệ thống, tôi muốn hệ thống tự động kiểm tra và ghi nhận vi phạm nếu người tham gia cuộc họp chưa nộp đánh giá sau 24 giờ kể từ khi cuộc họp kết thúc (thay vì phải đợi 72 giờ như trước đây), nhằm đảm bảo phản hồi đánh giá được thu thập kịp thời, nội dung cuộc họp còn mới mẻ và nâng cao kỷ luật trách nhiệm của các thành viên.

**Why this priority**: Đây là thay đổi nghiệp vụ cốt lõi theo yêu cầu của ban quản trị: rút ngắn thời gian chờ từ 3 ngày (72h) xuống 1 ngày (24h) để kịp thời tổng kết và kỷ luật đánh giá.

**Independent Test**: Tạo một cuộc họp có bật tính năng đánh giá với thời gian kết thúc đã qua 25 giờ (hoặc điều chỉnh thời gian kết thúc >24 giờ trước thời điểm hiện tại). Kích hoạt lượt quét kiểm tra vi phạm đánh giá. Xác nhận rằng hệ thống tự động ghi nhận vi phạm cho thành viên chưa nộp đánh giá và không ghi nhận vi phạm cho cuộc họp mới kết thúc dưới 24 giờ.

**Acceptance Scenarios**:

1. **Given** cuộc họp có yêu cầu đánh giá đã kết thúc hơn 24 giờ, **When** hệ thống thực hiện lượt quét kiểm tra định kỳ, **Then** tất cả thành viên thuộc diện bắt buộc đánh giá nhưng chưa hoàn thành sẽ bị ghi nhận một vi phạm chưa đánh giá cuộc họp.
2. **Given** cuộc họp có yêu cầu đánh giá kết thúc chưa đủ 24 giờ (ví dụ: mới kết thúc được 12 giờ hoặc 23 giờ), **When** hệ thống quét kiểm tra, **Then** hệ thống không ghi nhận bất kỳ vi phạm nào và cho phép người dùng tiếp tục hoàn thành đánh giá.
3. **Given** thành viên đã hoàn thành nộp đánh giá đầy đủ trước mốc 24 giờ, **When** hệ thống quét kiểm tra sau 24 giờ, **Then** thành viên này tuyệt đối không bị ghi nhận vi phạm.

---

### User Story 2 - Cập nhật thông điệp cảnh báo và thông báo vi phạm thể hiện mốc 24 giờ (Priority: P2)

Là Người dùng / Thành viên tham gia cuộc họp, tôi muốn các thông báo vi phạm và cảnh báo gửi đến tôi (qua Zalo, Discord, Web Push, Thông báo nội bộ) thể hiện chính xác mốc thời gian quy định là "trong vòng 24h" thay vì "trong vòng 72h", để tôi nắm rõ quy định mới và tránh hiểu nhầm về thời hạn xử lý.

**Why this priority**: Đảm bảo tính minh bạch, nhất quán giữa chính sách thực tế và nội dung thông báo gửi tới người dùng.

**Independent Test**: Kích hoạt việc ghi nhận một vi phạm quá hạn đánh giá cuộc họp; kiểm tra nội dung thông báo được phát đi tới người dùng, xác nhận thông điệp hiển thị rõ ràng cụm từ "trong vòng 24h" (hoặc "quá 24h"), không còn tồn tại con số 72h.

**Acceptance Scenarios**:

1. **Given** một vi phạm quá hạn đánh giá được tạo ra, **When** hệ thống gửi thông báo vi phạm tới người dùng qua các kênh thông báo, **Then** nội dung thông báo ghi rõ lý do vi phạm là chưa đánh giá cuộc họp trong vòng 24 giờ.
2. **Given** người dùng xem lịch sử vi phạm hoặc danh sách tác vụ định kỳ trên hệ thống quản trị, **Then** tên và mô tả tác vụ thể hiện chuẩn xác chu kỳ kiểm tra thời hạn 24 giờ.

---

### Edge Cases

- **Cuộc họp kết thúc trong giai đoạn chuyển giao**: Các cuộc họp đã kết thúc trước thời điểm cập nhật hệ thống và nằm trong khoảng thời gian từ 24h đến 72h trước đó sẽ được tự động xử lý ghi nhận vi phạm ngay trong lần quét kế tiếp theo đúng quy định mới.
- **Cuộc họp không bật tính năng đánh giá**: Các cuộc họp được cấu hình không yêu cầu đánh giá sẽ hoàn toàn bị bỏ qua trong quá trình quét, không tạo vi phạm dù đã kết thúc quá 24 giờ.
- **Cuộc họp bị hoãn hoặc chưa diễn ra**: Tuyệt đối không quét vi phạm cho các cuộc họp chưa tới thời điểm kết thúc.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI thay đổi thời hạn tối đa bắt buộc hoàn thành đánh giá cuộc họp từ 72 giờ thành 24 giờ tính từ mốc thời gian kết thúc cuộc họp.
- **FR-002**: Tác vụ quét vi phạm đánh giá định kỳ PHẢI sử dụng mốc chặn thời gian 24 giờ để lọc và xử lý các cuộc họp đã kết thúc quá thời hạn đánh giá.
- **FR-003**: Nội dung chi tiết của bản ghi vi phạm và thông điệp thông báo gửi tới người dùng PHẢI cập nhật mô tả thời hạn thành "trong vòng 24h".
- **FR-004**: Tên định danh và mô tả của tác vụ quét kiểm tra định kỳ trong hệ thống PHẢI được cập nhật đồng bộ sang mốc thời gian 24 giờ.
- **FR-005**: Mọi bài kiểm thử tự động (Unit / Integration tests) liên quan đến thời hạn đánh giá cuộc họp PHẢI được cập nhật tương ứng với mốc 24 giờ và vượt qua thành công.

### Key Entities

- **Cuộc họp (Meeting)**: Thực thể đại diện cho buổi họp/sinh hoạt, chứa thông tin thời gian bắt đầu, thời gian kết thúc, và cờ cho phép đánh giá.
- **Đánh giá cuộc họp (Meeting Evaluation)**: Bản ghi đánh giá do thành viên tham gia hoặc người phụ trách gửi lên.
- **Vi phạm (Violation)**: Bản ghi ghi nhận lỗi chưa đánh giá cuộc họp sau khi đã hết thời hạn 24 giờ, đi kèm điểm phạt hoặc mức cảnh cáo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% các cuộc họp có yêu cầu đánh giá kết thúc quá 24 giờ mà thành viên chưa nộp đánh giá sẽ được ghi nhận vi phạm trong lần quét tiếp theo.
- **SC-002**: 0 trường hợp thông báo vi phạm hoặc giao diện còn hiển thị mốc thời gian cũ "72h".
- **SC-003**: 100% các trường hợp đánh giá nộp trong vòng 24 giờ đầu tiên sau cuộc họp không bị ghi nhận vi phạm nhầm.
- **SC-004**: Toàn bộ bộ kiểm thử tự động của miền nghiệp vụ cuộc họp và vi phạm vượt qua thành công sau khi cập nhật.

## Assumptions

- Quy định 24 giờ áp dụng đồng nhất cho tất cả các cuộc họp có bật đánh giá trong toàn hệ thống.
- Chu kỳ chạy của tác vụ quét định kỳ (mỗi giờ 1 lần) vẫn tiếp tục duy trì để kịp thời phát hiện các cuộc họp vừa vượt qua mốc 24 giờ.
