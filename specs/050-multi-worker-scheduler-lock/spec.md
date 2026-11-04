# Feature Specification: Đồng Bộ Điều Phối Tác Vụ Nền Trong Môi Trường Đa Tiến Trình (Multi-Worker Scheduler Synchronization)

**Feature Branch**: `050-multi-worker-scheduler-lock`

**Created**: 2026-11-05

**Status**: Draft

**Input**: User description: "Tôi muốn tăng số worker lên để chạy nhiều request cùng 1 lúc, nhưng vấn đề là nó sẽ bị trùng job scan, tôi phải làm sao? Lược bỏ hoàn toàn ENABLE_SCHEDULER. Mọi worker cứ chạy lên là tự kết nối Redis tranh chấp quyền, không cần thêm biến cấu hình nào ngoài thông tin kết nối Redis."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Khả năng mở rộng tiến trình xử lý API mà không nhân bản tác vụ định kỳ (Priority: P1) 🎯 MVP

Là Quản trị viên hệ thống, tôi muốn tăng số lượng tiến trình phục vụ (workers) trong máy chủ ứng dụng để xử lý đồng thời nhiều yêu cầu của người dùng, nhưng hệ thống chỉ cho phép duy nhất một tiến trình đảm nhận việc quét và chạy các tác vụ định kỳ (background scheduler), nhằm loại bỏ hoàn toàn tình trạng gửi trùng lặp thông báo hoặc quét lặp dữ liệu mà không cần thêm bất kỳ cờ cấu hình thủ công nào.

**Why this priority**: Đây là mục tiêu cốt lõi của người dùng: tăng năng lực chịu tải API của hệ thống (bằng cách nâng số lượng worker trong Dockerfile / Uvicorn) mà không gây ra tác dụng phụ nghiêm trọng là spam thông báo và xung đột dữ liệu từ các job nền chạy song song.

**Independent Test**: Cấu hình hệ thống khởi chạy với nhiều tiến trình phục vụ web (ví dụ: 4 workers trong container). Chờ hoặc kích hoạt một tác vụ quét định kỳ (nhắc nhở công việc, điểm danh, tính điểm). Xác nhận rằng chỉ có duy nhất 1 thông báo/kết quả được phát đi trong toàn hệ thống thay vì nhân lên theo số lượng worker.

**Acceptance Scenarios**:

1. **Given** hệ thống được khởi động với nhiều worker đồng thời (từ 2 worker trở lên), **When** đến mốc thời gian thực thi của một tác vụ định kỳ (nhắc nhở công việc, điểm danh, tính điểm), **Then** chỉ có duy nhất một worker được phép thực thi tác vụ đó và kết quả tác vụ chỉ được phát đi 1 lần.
2. **Given** hệ thống đang nhận lượng lớn yêu cầu API đồng thời từ người dùng, **When** các worker cùng chia sẻ tải xử lý yêu cầu, **Then** các tác vụ nền vẫn được kích hoạt đúng lịch trình mà không làm gián đoạn việc phục vụ yêu cầu hay nhân bản tác vụ giữa các worker.

---

### User Story 2 - Tự động chuyển giao quyền điều phối khi tiến trình phụ trách gặp sự cố (Priority: P2)

Là Quản trị viên hệ thống, tôi muốn nếu tiến trình worker đang giữ quyền chạy tác vụ định kỳ bị dừng, khởi động lại hoặc gặp sự cố bất ngờ, một tiến trình worker khả dụng khác sẽ tự động tiếp quản vai trò chạy tác vụ định kỳ, đảm bảo các tác vụ quét thời hạn không bị gián đoạn hay bỏ sót.

**Why this priority**: Đảm bảo tính sẵn sàng cao (High Availability) và tự phục hồi (Self-healing). Nếu một worker chết mà quyền không được chuyển giao, toàn bộ tác vụ nền sẽ bị đình trệ.

**Independent Test**: Khởi chạy hệ thống với từ 2 worker trở lên. Xác định worker đang giữ quyền điều phối tác vụ nền và chủ động dừng tiến trình đó (kill process). Xác nhận một worker còn lại tự động nhận quyền và tiếp tục kích hoạt các tác vụ theo lịch trình đã định.

**Acceptance Scenarios**:

1. **Given** một worker đang chịu trách nhiệm chạy các tác vụ định kỳ, **When** tiến trình worker này bị dừng đột ngột hoặc kết thúc, **Then** một worker khác đang hoạt động trong cụm sẽ tự động phát hiện và tiếp quản quyền điều phối lịch trình.
2. **Given** worker cũ được phục hồi hoặc khởi động lại, **When** worker này tham gia lại vào cụm tiến trình, **Then** nó nhận diện đã có worker khác đang giữ quyền và chỉ hoạt động ở chế độ phục vụ yêu cầu thông thường, không can thiệp vào tác vụ định kỳ.

---

### Edge Cases

- **Khởi động đồng thời cùng lúc**: Khi nhiều worker cùng khởi động tại cùng một thời điểm chính xác (cold start), cơ chế tranh chấp quyền phải đảm bảo tính nguyên tử (atomic), tuyệt đối không xảy ra tình trạng cả hai worker đều cho rằng mình đã giành được quyền điều phối.
- **Tác vụ chạy kéo dài quá chu kỳ tiếp theo**: Nếu một tác vụ quét dữ liệu lớn kéo dài hơn khoảng cách giữa 2 lần quét (ví dụ quét mất 35 phút trong khi chu kỳ là 30 phút), hệ thống phải ngăn chặn việc kích hoạt chồng lấn (overlapping execution) của cùng một tác vụ.
- **Mất kết nối tài nguyên khóa tạm thời**: Nếu cơ chế đồng bộ gặp gián đoạn tạm thời, các tiến trình phải xử lý lỗi mềm dẻo (graceful degradation), ghi nhật ký cảnh báo và tự động thử lại thay vì làm sập toàn bộ tiến trình phục vụ web.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI hỗ trợ khởi chạy an toàn trên môi trường nhiều tiến trình phục vụ (multi-worker) mà không gây ra hiện tượng thực thi trùng lặp các tác vụ định kỳ.
- **FR-002**: Hệ thống PHẢI đảm bảo chỉ có duy nhất MỘT tiến trình được cấp quyền điều phối và kích hoạt các tác vụ nền tại bất kỳ thời điểm nào (Single Leader Election / Exclusive Execution) thông qua Redis.
- **FR-003**: Hệ thống PHẢI có cơ chế phát hiện và tự động giải phóng quyền điều phối khi tiến trình nắm quyền kết thúc hoạt động hoặc gặp sự cố, cho phép tiến trình khả dụng khác tiếp quản tự động.
- **FR-004**: Mọi worker khởi chạy PHẢI tự động tham gia cơ chế điều phối qua Redis mà không đòi hỏi bất kỳ cờ cấu hình bật/tắt thủ công phức tạp nào.
- **FR-005**: Mỗi tác vụ định kỳ PHẢI có cơ chế bảo vệ chống thực thi chồng chéo (coalescing / non-concurrency) trong trường hợp lần chạy trước đó chưa hoàn thành khi đến chu kỳ kế tiếp.
- **FR-006**: Quá trình kiểm tra và xác lập quyền điều phối tác vụ PHẢI diễn ra nhanh chóng, không làm chậm trễ thời gian khởi động hoặc gây nghẽn tiến trình xử lý yêu cầu của máy chủ ứng dụng.

### Key Entities

- **Scheduler Coordinator**: Bộ điều phối trung tâm chịu trách nhiệm quản lý vòng đời của bộ lịch trình tác vụ, xác định tiến trình nào có quyền thực thi và giải phóng tài nguyên khi ứng dụng tắt.
- **Distributed Execution Lock**: Khóa đồng bộ độc quyền đại diện cho quyền điều phối tác vụ nền trong môi trường đa tiến trình/đa máy chủ, đảm bảo tính nguyên tử và chỉ cho phép một chủ thể nắm giữ tại một thời điểm trên Redis.
- **Scheduled Job Descriptor**: Bản mô tả tác vụ định kỳ, bao gồm định danh tác vụ, chu kỳ kích hoạt, trạng thái đang thực thi (idle / running), và tham số điều phối.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% các tác vụ định kỳ chỉ được thực thi đúng 1 lần trên toàn hệ thống trong mỗi chu kỳ đã định, bất kể số lượng worker tăng lên bao nhiêu (2, 4, 8 workers).
- **SC-002**: Tỷ lệ thông báo gửi trùng lặp do nguyên nhân đa tiến trình giảm về chính xác 0%.
- **SC-003**: Năng lực xử lý yêu cầu đồng thời của máy chủ web tăng tỷ lệ thuận với số lượng worker cấu hình trong khi các tác vụ định kỳ vẫn hoạt động chính xác.
- **SC-004**: Thời gian phát hiện sự cố và tiếp quản quyền điều phối tác vụ diễn ra trong vòng dưới 60 giây khi tiến trình chính bị dừng đột ngột.
- **SC-005**: Khởi động cụm đa worker hoàn tất ổn định mà không xảy ra xung đột khóa hoặc lỗi deadlock giữa các tiến trình.

## Assumptions

- Môi trường máy chủ ứng dụng sử dụng kiến trúc nhiều tiến trình (Uvicorn multi-worker trong Docker container).
- Dịch vụ Redis 7 dùng chung mạng nội bộ với backend để quản lý khóa phân tán.
- Các tác vụ nền được thiết kế để hoàn thành trong khoảng thời gian hợp lý so với chu kỳ kích hoạt của chúng.
