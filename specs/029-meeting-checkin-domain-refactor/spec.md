# Feature Specification: Unified Meeting Check-In Domain Entity Refactor

## 1. Problem Statement
Hiện tại trong hệ thống `dut-ai-manager`, logic điểm danh (Check-in) buổi sinh hoạt đang phân mảnh và lặp lại trên nhiều tầng và nhiều use case khác nhau:
- **`CheckInUseCase`** (quét khuôn mặt / bulk qua Camera AI / Robot): tự tính toán logic đi trễ `is_late`, dùng `now` của server thay vì `check_in_dt` để tìm khung giờ họp, bỏ qua không ghi nhận `check_in_at` nếu học viên đã có trạng thái `LATE_EXCUSED`, và không persist `client_event_id` vào DB.
- **`CheckInWithCardUseCase`** (quẹt thẻ NFC/RFID): tự tính toán `is_late`, tự xử lý status.
- **`UpdateParticipantStatusUseCase`** (điểm danh thủ công trên web): tự parse thời gian, gán fallback start_time.
- **`MeetingParticipant` Domain Entity**: chứa phương thức `check_in()` anemic, return sớm nếu status là `JOINED`, `LATE_EXCUSED`, `LATE_UNEXCUSED`, `COMPLETED` khiến học viên có đơn xin phép đi trễ khi có mặt thực tế bị mất dấu thời gian `check_in_at` (vẫn là `None`).

Kiến trúc này vi phạm nguyên lý **Clean Architecture & Practical DDD Boundaries (Principle I)** và **Single Source of Truth (Principle X)** trong Hiến pháp dự án.

## 2. Business Goals & User Stories

### User Story 1: Domain-Centric Check-In Rules (P1)
**Là một** nhà phát triển hệ thống và quản trị viên,  
**Tôi muốn** mọi luật nghiệp vụ liên quan đến điểm danh (xác định trạng thái đi trễ, bảo lưu đơn xin phép có lý do, cập nhật mốc thời gian và bằng chứng ảnh) được đóng gói tập trung duy nhất bên trong Domain Entity `MeetingParticipant`,  
**Để** loại bỏ toàn bộ duplicate logic giữa các use case và ngăn ngừa triệt để lỗi mất dữ liệu `check_in_at`.

- **Acceptance Criteria**:
  1. `MeetingParticipant.record_check_in(...)` nhận `check_in_time`, `meeting_start_time`, `image_url` (optional), `client_event_id` (optional).
  2. Nếu học viên đã `COMPLETED` (đã checkout / kết thúc): từ chối check-in với thông báo rõ ràng.
  3. Nếu học viên có đơn xin đi trễ đã duyệt (`status == LATE_EXCUSED`): luôn ghi nhận `check_in_at = check_in_time`, lưu `link_image` và giữ nguyên trạng thái `LATE_EXCUSED` (không bị ghi đè thành `JOINED` hoặc `LATE_UNEXCUSED`).
  4. Nếu học viên đến trễ (`check_in_time > meeting_start_time`): cập nhật trạng thái `LATE_UNEXCUSED` (nếu chưa có phép), ghi nhận `check_in_at` và `link_image`.
  5. Nếu học viên đến đúng giờ (`check_in_time <= meeting_start_time`): cập nhật trạng thái `JOINED`, ghi nhận `check_in_at` và `link_image`.
  6. Luôn cập nhật `client_event_id` (nếu được cung cấp) phục vụ chống trùng lặp sự kiện.

### User Story 2: Orchestration Refactoring in Use Cases (P1)
**Là một** hệ thống tiếp nhận điểm danh từ nhiều nguồn (AI Camera, Thẻ RFID, Web Admin),  
**Tôi muốn** các Use Case (`CheckInUseCase`, `CheckInWithCardUseCase`, `UpdateParticipantStatusUseCase`) chỉ đóng vai trò Orchestrator mỏng (thin coordinator),  
**Để** ủy quyền 100% quyết định trạng thái và mốc thời gian cho Domain Entity, sau đó gọi Repo lưu trữ và phát tán EventBus.

- **Acceptance Criteria**:
  1. `CheckInUseCase`: Sử dụng `check_in_dt` (chuẩn hóa UTC từ `client_time` hoặc `now`) làm mốc tính `window_start = check_in_dt - 30m` và `window_end = check_in_dt + 30m`, khắc phục lỗi mất buổi họp khi thiết bị gửi trễ.
  2. `CheckInWithCardUseCase`: Gọi trực tiếp phương thức nghiệp vụ của Domain Entity, giữ nguyên luồng TTS.
  3. Tất cả Use Case phát tán `ParticipantCheckedIn` với cờ `is_late` và `check_in_at` chính xác được trả về từ Domain Entity.

### User Story 3: Repository Persistence Completeness (P1)
**Là một** cơ sở dữ liệu hệ thống,  
**Tôi muốn** `ParticipantRepository.save()` lưu trữ đầy đủ mọi thuộc tính của Domain Participant vào ORM Model (`client_event_id`, `check_in_at`, `check_out_at`, `status`, `link_image`),  
**Để** cơ chế chống trùng lặp `client_event_id` và lịch sử điểm danh được duy trì bền vững trong Database.

## 3. Non-Functional Requirements
- **Hiệu năng & Toàn vẹn UTC**: Mọi timestamp xử lý phải là Timezone-Aware UTC tuân thủ Hiến pháp v1.6.0.
- **Kiểm thử**: Viết unit test bao phủ toàn bộ các kịch bản check-in của `MeetingParticipant` (đúng giờ, trễ có phép, trễ không phép, đã checkout, ghi đè ảnh) và regression test cho các Use Case.
- **Zero Regression**: Đảm bảo 152/152 unit tests hiện tại tiếp tục pass 100%.
