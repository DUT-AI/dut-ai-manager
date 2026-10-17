# Feature Specification: Tái cấu trúc Định danh Xác thực (Auth Principal Refactor)

**Feature Branch**: `010-auth-principal-refactor`

**Created**: 2026-10-17

**Status**: Draft

**Input**: User description: "hãy refactor lại giúp tôi nhé - tách riêng decoder_entity (AuthPrincipal) thay vì dùng UserEntity trong luồng giải mã token/API key"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tách biệt Định danh Xác thực và Thực thể Người dùng (Priority: P1)

Hệ thống cung cấp một mô hình định danh xác thực độc lập (`AuthPrincipal` / `DecodedIdentity`) để đại diện cho chủ thể đang thực hiện yêu cầu (gồm cả người dùng cá nhân lẫn dịch vụ/máy móc tích hợp qua API Key), chấm dứt việc giả lập thực thể người dùng (`UserEntity`) với định danh giả (`id=0`) và dữ liệu ảo.

**Why this priority**: Đây là nền tảng cốt lõi giải quyết rủi ro toàn vẹn dữ liệu (tránh lưu `user_id = 0` vào cơ sở dữ liệu hoặc xung đột khóa ngoại), đồng thời tuân thủ nguyên tắc phân định ranh giới kiến trúc sạch (Clean Architecture).

**Independent Test**: Có thể kiểm thử độc lập bằng cách gửi yêu cầu sử dụng API Key hợp lệ và yêu cầu sử dụng JWT hợp lệ: hệ thống phân định chính xác loại chủ thể, quyền hạn và danh tính mà không tạo ra bất kỳ đối tượng `UserEntity` giả lập nào trong phiên làm việc.

**Acceptance Scenarios**:

1. **Given** một yêu cầu từ dịch vụ bên ngoài mang mã API Key hợp lệ, **When** hệ thống xác thực và cấp quyền, **Then** chủ thể xác thực được nhận diện là loại Dịch vụ/Hệ thống (`API_KEY`), nạp đầy đủ quyền hạn liên kết từ vai trò, và không gán định danh người dùng giả vào ngữ cảnh kiểm toán cơ sở dữ liệu.
2. **Given** một yêu cầu từ người dùng mang mã JWT Access Token hợp lệ, **When** hệ thống xác thực, **Then** chủ thể xác thực được nhận diện là loại Người dùng (`USER`), chứa đầy đủ mã định danh người dùng thực tế, email, danh sách vai trò và quyền hạn được mã hóa trong token.

---

### User Story 2 - Kiểm tra Quyền hạn Nhanh từ Ngữ cảnh Xác thực (Priority: P2)

Hệ thống cho phép các điểm cuối (endpoints) kiểm tra quyền truy cập (RBAC) trực tiếp từ thông tin quyền hạn của chủ thể xác thực đã được giải mã, không bắt buộc phải truy vấn toàn bộ bản ghi người dùng từ cơ sở dữ liệu nếu yêu cầu đó chỉ phục vụ mục đích phân quyền.

**Why this priority**: Cải thiện đáng kể hiệu năng phản hồi, giảm thiểu các truy vấn IO đọc dữ liệu người dùng dư thừa trên phần lớn các điểm cuối của hệ thống.

**Independent Test**: Gửi yêu cầu với JWT token chứa danh sách quyền hạn hợp lệ đến các điểm cuối được bảo vệ bằng quyền: hệ thống xác thực quyền thành công và cho phép truy cập mà không kích hoạt truy vấn đọc chi tiết bảng người dùng.

**Acceptance Scenarios**:

1. **Given** chủ thể xác thực sở hữu quyền hợp lệ cho điểm cuối được yêu cầu, **When** gửi yêu cầu truy cập, **Then** hệ thống phê duyệt truy cập tức thì dựa trên dữ liệu quyền của chủ thể.
2. **Given** chủ thể xác thực không sở hữu quyền cần thiết và không có vai trò Quản trị viên, **When** gửi yêu cầu truy cập, **Then** hệ thống từ chối với mã lỗi 403 Forbidden kèm thông điệp về quyền bị thiếu.
3. **Given** chủ thể xác thực có vai trò Quản trị viên (Admin), **When** truy cập bất kỳ điểm cuối được bảo vệ nào, **Then** hệ thống tự động phê duyệt truy cập.

---

### User Story 3 - Bảo toàn Tương thích cho Nghiệp vụ Yêu cầu Hồ sơ Cá nhân (Priority: P3)

Hệ thống cung cấp cơ chế phân định rõ ràng giữa "Yêu cầu chỉ cần định danh và quyền" và "Yêu cầu nghiệp vụ cần thực thể hồ sơ cá nhân đầy đủ", đảm bảo các điểm cuối cần thông tin chi tiết người dùng (như liên kết Zalo, ảnh đại diện, số điện thoại) vẫn lấy được dữ liệu chính xác, đồng thời tự động từ chối nếu bị gọi bởi các khóa máy móc API Key không có hồ sơ cá nhân.

**Why this priority**: Đảm bảo an toàn nghiệp vụ và ngăn ngừa hồi quy logic trên hơn 30 điểm cuối hiện hữu đang phụ thuộc vào dữ liệu người dùng.

**Independent Test**: Gửi yêu cầu đến các điểm cuối thao tác hồ sơ cá nhân (ví dụ xem thông tin bản thân): người dùng hợp lệ nhận được dữ liệu đầy đủ, trong khi yêu cầu từ API Key bị từ chối rõ ràng rằng tính năng chỉ dành cho tài khoản người dùng cá nhân.

**Acceptance Scenarios**:

1. **Given** một điểm cuối yêu cầu hồ sơ người dùng đầy đủ, **When** được gọi bởi chủ thể là người dùng hợp lệ, **Then** hệ thống nạp thực thể người dùng đầy đủ từ cơ sở dữ liệu để phục vụ nghiệp vụ.
2. **Given** một điểm cuối yêu cầu hồ sơ người dùng đầy đủ, **When** bị gọi bởi một API Key máy móc, **Then** hệ thống từ chối với mã lỗi 403 Forbidden và thông báo rõ ràng thao tác chỉ áp dụng cho tài khoản người dùng.

---

### Edge Cases

- **Chủ thể API Key thao tác dữ liệu gắn liền với chủ sở hữu**: Khi một dịch vụ bên ngoài dùng API Key cố gắng gọi điểm cuối yêu cầu gán người sở hữu là chính mình (ví dụ `get_my_homeworks` hoặc tạo bài tập cho chính mình), hệ thống từ chối lịch sự bằng lỗi xác thực nghiệp vụ thay vì truy vấn dữ liệu với `id=0`.
- **Token JWT hết hạn hoặc không hợp lệ**: Hệ thống dừng xử lý ngay lập tức và trả về mã lỗi 401 Unauthorized trước khi đi vào bất kỳ logic nghiệp vụ nào.
- **API Key không tồn tại, sai định dạng hoặc bị vô hiệu hóa**: Hệ thống trả về mã lỗi 401 Unauthorized và từ chối yêu cầu.
- **Chủ thể có quyền nhưng người dùng đã bị xóa hoặc vô hiệu hóa trong cơ sở dữ liệu**: Khi điểm cuối yêu cầu nạp thực thể người dùng đầy đủ, hệ thống phát hiện trạng thái không khả dụng và từ chối với lỗi 401 Unauthorized.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI định nghĩa mô hình dữ liệu định danh xác thực (`AuthPrincipal`) độc lập hoàn toàn với thực thể nghiệp vụ người dùng (`UserEntity`).
- **FR-002**: Mô hình định danh xác thực PHẢI phân biệt rõ ràng hai nhóm chủ thể: Người dùng thực tế (`USER`) và Khóa ứng dụng/Hệ thống (`API_KEY`).
- **FR-003**: Hệ thống TUYỆT ĐỐI KHÔNG ĐƯỢC khởi tạo thực thể người dùng giả lập (`UserEntity`) với định danh bằng 0 (`id=0`) hoặc thư điện tử giả (`system+...@dutai.site`) để đại diện cho API Key.
- **FR-004**: Mô hình định danh xác thực PHẢI cung cấp phương thức kiểm tra quyền hạn (`has_permission`), trong đó tự động thông qua nếu chủ thể sở hữu vai trò Quản trị viên (Admin).
- **FR-005**: Hệ thống PHẢI hỗ trợ cơ chế phụ thuộc (dependency) trích xuất chủ thể xác thực (`CurrentUser` / `CurrentPrincipal`) từ token hoặc API Key cho các bộ điều khiển (controllers).
- **FR-006**: Hệ thống PHẢI cung cấp cơ chế phụ thuộc riêng biệt khi cần truy xuất thực thể người dùng cơ sở dữ liệu (`UserEntity`), và tự động chặn các yêu cầu xuất phát từ API Key máy móc.
- **FR-007**: Ngữ cảnh lưu vết kiểm toán (`contextvars.current_user_id`) CHỈ ĐƯỢC gán giá trị định danh khi chủ thể là người dùng thực tế có mã định danh hợp lệ, và được đặt là `None` đối với các thao tác của API Key để tránh xung đột khóa ngoại cơ sở dữ liệu.
- **FR-008**: Toàn bộ các cơ chế kiểm tra quyền truy cập hiện hữu (`hasPermission`, `PermissionChecker`) PHẢI tương thích hoàn toàn với mô hình định danh xác thực mới mà không cần viết lại hàng loạt controller.

### Key Entities *(include if feature involves data)*

- **AuthPrincipal (Chủ thể Định danh Xác thực)**: Mô hình dữ liệu phi thực thể cơ sở dữ liệu, đại diện cho đối tượng đã được xác thực an toàn qua chữ ký hoặc khóa bí mật. Chứa: loại chủ thể (`actor_type`), mã định danh đối tượng (`actor_id`), tên hiển thị (`name`), thư điện tử (`email`), danh sách vai trò (`role_names`) và tập hợp mã quyền hạn (`permissions`).
- **UserEntity (Thực thể Người dùng Cơ sở Dữ liệu)**: Thực thể nghiệp vụ thuần túy của miền dữ liệu Người dùng, chứa đầy đủ thông tin cá nhân và các liên kết nghiệp vụ mở rộng (Zalo, Discord, thẻ điểm danh, ảnh đại diện, số điện thoại).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Loại bỏ 100% việc tạo ra các thực thể người dùng giả với `id = 0` hoặc email giả lập trong toàn bộ tầng xác thực của hệ thống.
- **SC-002**: Đạt 0% lỗi xung đột khóa ngoại (Foreign Key constraint violations) bắt nguồn từ các thao tác hệ thống máy móc do mang định danh người dùng không hợp lệ.
- **SC-003**: 100% các điểm cuối chỉ yêu cầu kiểm tra quyền hạn thực thi kiểm tra thành công trực tiếp từ dữ liệu định danh đã giải mã mà không cần truy vấn bảng người dùng trong cơ sở dữ liệu đối với token hợp lệ.
- **SC-004**: Đảm bảo 100% bộ kiểm thử tự động hiện tại (test suite) vượt qua thành công, không gây hồi quy (Zero Regression) cho các tính năng người dùng hiện có.

## Assumptions

- Mã JWT Access Token hiện tại đã chứa đầy đủ danh sách vai trò (`roles`) và quyền hạn (`permissions`) của người dùng tại thời điểm đăng nhập/cấp mã theo định dạng `AccessTokenPayload`.
- Các điểm cuối hiện hữu đang sử dụng `current_user.id` cho các tác vụ người dùng cá nhân (như danh sách bài tập của tôi, điểm thưởng cá nhân) cần được bảo vệ để chỉ cho phép chủ thể loại Người dùng (`USER`) thực hiện.
- Ngữ cảnh kiểm toán (`set_current_user_id`) cho phép nhận giá trị `None` hoặc số nguyên hợp lệ trong cấu trúc cơ sở dữ liệu kiểm toán hiện tại.
