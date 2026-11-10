# Feature Specification: Tách biệt Soft Delete và Hỗ trợ Khóa chính UUID cho Domain Model

**Feature Branch**: `059-uuid-optional-soft-delete`

**Created**: 2026-11-10

**Status**: Draft

**Input**: User description: "Hiện tại tôi có thấy 1 vấn đề là model, entity nào cũng có trường id là int và is_deleted, tôi mong muốn những model sau này dùng uuid và không phải model nào cũng cần is_deleted á"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Hỗ trợ Khóa chính UUID linh hoạt cho Model và Entity mới (Priority: P1) 🎯 MVP

Là một kỹ sư phát triển tính năng mới, tôi muốn có thể định nghĩa Domain Entity và ORM Model với khóa chính là UUID thay vì bắt buộc kiểu số nguyên `int`, nhằm tránh việc phơi bày ID tuần tự (enumeration attack), hỗ trợ sinh ID phía client/phân tán trước khi lưu vào cơ sở dữ liệu, đồng thời không làm ảnh hưởng đến các model hiện tại đang dùng `int`.

**Why this priority**: Đây là nền tảng cốt lõi cho các module và bảng dữ liệu mới trong tương lai. Nếu không hỗ trợ UUID ở tầng Base Entity/Model và Base Repository, các tính năng mới sẽ tiếp tục bị ép buộc theo cấu trúc cũ.

**Independent Test**: Có thể kiểm thử độc lập bằng cách tạo một model mẫu sử dụng UUID làm khóa chính, thực hiện thêm mới, truy vấn theo ID và danh sách qua BaseRepository mà không gặp lỗi type mismatch hoặc casting.

**Acceptance Scenarios**:

1. **Given** một domain entity mới được định nghĩa với khóa chính `id: UUID`, **When** lưu trữ qua repository vào database, **Then** bản ghi được lưu thành công với kiểu UUID nguyên bản và trả về entity có ID dạng UUID.
2. **Given** một bản ghi đã tồn tại với khóa chính UUID, **When** gọi `repository.get_by_id(uuid_value)`, **Then** hệ thống tìm kiếm chính xác bản ghi đó và ánh xạ về Domain Entity tương ứng.
3. **Given** các domain entity hiện có (như `User`, `Meeting`, `Homework` đang dùng `id: int`), **When** hệ thống thực hiện các thao tác CRUD hiện tại, **Then** mọi chức năng hoạt động bình thường, không có bất kỳ xung đột hoặc hồi quy nào.

---

### User Story 2 - Tách biệt cơ chế Xóa mềm (Soft Delete) thành thành phần tùy chọn (Priority: P2)

Là một kỹ sư phát triển, tôi muốn trường `is_deleted` và logic lọc xóa mềm trở thành một mixin/tính năng độc lập có thể tùy chọn (opt-in) thay vì bị gộp cưỡng bức vào Timestamp/Base Entity, để những model dữ liệu tạm thời (transient), log sự kiện, hoặc bảng quan hệ trung gian không bị lãng phí tài nguyên và có thể xóa cứng (hard delete) sạch sẽ.

**Why this priority**: Việc cưỡng bức `is_deleted` trên mọi bảng khiến cơ sở dữ liệu phình to với các dữ liệu rác không cần lưu trữ lịch sử, đồng thời làm phức tạp hóa các câu lệnh SQL với mệnh đề `WHERE is_deleted = false` không cần thiết.

**Independent Test**: Có thể kiểm thử độc lập bằng cách tạo 2 model: một model không có `is_deleted` và một model có `is_deleted`. Khi thực hiện truy vấn và thao tác xóa trên từng model, hành vi lọc và xóa sẽ hoạt động đúng theo cấu hình của từng model.

**Acceptance Scenarios**:

1. **Given** một model không khai báo xóa mềm, **When** gọi truy vấn `get_all()` hoặc `get_paged()`, **Then** câu lệnh truy vấn không chứa điều kiện `WHERE is_deleted = false` và trả về đầy đủ các bản ghi thực tế.
2. **Given** một model không khai báo xóa mềm, **When** thực hiện thao tác xóa một bản ghi, **Then** bản ghi đó được xóa vĩnh viễn (hard delete) khỏi cơ sở dữ liệu.
3. **Given** một model có khai báo xóa mềm (sử dụng trait/mixin xóa mềm), **When** truy vấn mặc định, **Then** hệ thống tự động lọc bỏ các bản ghi đã xóa mềm (`is_deleted = true`).
4. **Given** một model có khai báo xóa mềm, **When** thực hiện xóa mềm, **Then** cờ `is_deleted` được đánh dấu là `True` mà không xóa bản ghi vật lý.

---

### User Story 3 - Cung cấp Kiến trúc Base Composable cho Nhà phát triển (Priority: P3)

Là một kỹ sư phần mềm khi xây dựng module mới, tôi muốn có các lớp cơ sở (Base Classes) và Mixins rõ ràng, có tính module hóa cao (Modular & Composable) để có thể tùy ý kết hợp: (Khóa UUID hoặc Int) + (Timestamps) + (Audit User) + (Soft Delete hoặc Hard Delete) theo đúng nhu cầu nghiệp vụ mà không cần viết lại mã nguồn nền tảng.

**Why this priority**: Tăng tốc độ phát triển cho các module sau này, chuẩn hóa cấu trúc toàn dự án và tuân thủ nguyên lý Clean Architecture & Single Responsibility Principle.

**Independent Test**: Có thể kiểm thử độc lập bằng cách lập tài liệu hướng dẫn và unit test cho các tổ hợp cấu hình base entity / model khác nhau.

**Acceptance Scenarios**:

1. **Given** nhà phát triển tạo một bảng chỉ cần `id: UUID` và thời gian tạo `created_at`, **When** kế thừa từ các composable mixin tương ứng, **Then** model chỉ chứa đúng các cột này mà không bị dư thừa `is_deleted`, `updated_by` hay `created_by`.
2. **Given** nhà phát triển tạo một bảng cần đầy đủ audit trail và soft delete với `id: UUID`, **When** áp dụng tổ hợp mixin audit, **Then** model có đầy đủ các trường cần thiết một cách nhất quán.

---

### Edge Cases

- **Truy vấn nhầm kiểu ID**: Khi truyền chuỗi không hợp lệ vào repository yêu cầu khóa chính UUID (ví dụ truyền chuỗi không đúng định dạng UUID hoặc số nguyên vào trường UUID), hệ thống phải bắt lỗi và thông báo lỗi định dạng rõ ràng (Validation Error / 400 Bad Request) thay vì sập database query với lỗi 500.
- **Thao tác xóa mềm trên Model không hỗ trợ**: Nếu một service/usecase cố gắng gọi hàm xóa mềm trên một repository quản lý model không có trường `is_deleted`, hệ thống phải ném lỗi tường minh (`NotImplementedError` hoặc `InvalidOperationException`) ngay tại tầng domain/repository.
- **Quan hệ Khóa ngoại với bảng cũ**: Khi một model mới dùng khóa chính UUID có quan hệ khóa ngoại (Foreign Key) tới bảng cũ (ví dụ bảng `users` có `id: int`), trường quan hệ phải giữ nguyên kiểu `int` cho foreign key (`created_by: int`, `user_id: int`), không được ép đổi sai kiểu.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI cung cấp lớp cơ sở Domain Entity hỗ trợ khóa chính UUID (`id: UUID`), đồng thời duy trì lớp cơ sở hiện tại cho các entity dùng khóa chính số nguyên (`id: int`) để đảm bảo tính tương thích ngược hoàn toàn.
- **FR-002**: Hệ thống PHẢI chuẩn hóa UUIDv7 (Time-ordered UUID) làm phiên bản mặc định cho các model và entity mới. UUIDv7 được sắp xếp tuần tự theo thời gian nhằm tối ưu hóa index B-Tree trong cơ sở dữ liệu PostgreSQL, giảm thiểu phân mảnh trang dữ liệu (page fragmentation) khi bảng có tần suất ghi cao.
- **FR-003**: Hệ thống PHẢI tách biệt trường `is_deleted` khỏi các mixin thời gian cơ bản (`TimestampMixin`), cho phép các model mới tùy chọn có hoặc không có tính năng xóa mềm (Soft Delete).
- **FR-004**: Tầng ORM và BaseRepository PHẢI tự động nhận biết model có hỗ trợ xóa mềm hay không:
  - Nếu model CÓ hỗ trợ xóa mềm: Tự động lọc `is_deleted = false` trong các câu lệnh truy vấn mặc định.
  - Nếu model KHÔNG hỗ trợ xóa mềm: Không sinh điều kiện lọc `is_deleted` trong câu lệnh SQL.
- **FR-005**: BaseRepository PHẢI phân tách rạch ròi hai phương thức xóa:
  - `soft_delete(id/entity)`: Đánh dấu xóa mềm (`is_deleted = True`), ném ngoại lệ rõ ràng (`NotImplementedError` hoặc `InvalidOperationException`) nếu model không hỗ trợ xóa mềm.
  - `hard_delete(id/entity)`: Thực hiện xóa vật lý vĩnh viễn (`session.delete(model)`) bản ghi khỏi cơ sở dữ liệu (áp dụng được cho cả model có và không có xóa mềm khi muốn dọn dẹp triệt để).
- **FR-006**: BaseRepository PHẢI là generic trên kiểu khóa chính (`TId`), cho phép hỗ trợ đồng thời cả `int` (cho model cũ) và `UUID` (cho model mới) mà không cần tạo 2 class BaseRepository riêng biệt gây phân mảnh mã nguồn.
- **FR-007**: Hệ thống PHẢI đảm bảo các trường kiểm tra người tạo/cập nhật (`created_by`, `updated_by`) có thể hoạt động linh hoạt khi liên kết với bảng `users` hiện tại (vốn dùng `id: int`).

---

### Key Entities *(include if feature involves data)*

- **BaseEntity[TId] / BaseUuidEntity**: Lớp cơ sở Domain Entity thuần túy (Pydantic), cho phép xác định kiểu `id` là `UUID` hoặc `int`. Không bắt buộc chứa `is_deleted`.
- **SoftDeleteEntityMixin**: Mixin của Domain Entity bổ sung trường `is_deleted: bool = False` cho các domain thực sự cần lưu vết lịch sử xóa.
- **SQLAlchemyTimestampMixin**: Mixin ORM thuần túy chỉ quản lý `created_at` và `updated_at` (chuẩn UTC timezone-aware), không chứa `is_deleted`.
- **SQLAlchemySoftDeleteMixin**: Mixin ORM độc lập bổ sung cột `is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)`.
- **SQLAlchemyAuditMixin**: Mixin ORM quản lý người tạo và cập nhật (`created_by`, `updated_by` trỏ tới `users.id`).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% các model mới trong tương lai có thể khai báo khóa chính UUID mà không cần workaround hoặc ghi đè kiểu dữ liệu thủ công.
- **SC-002**: 100% các câu lệnh truy vấn (`get_by_id`, `get_all`, `get_paged`) đối với các bảng không sử dụng soft-delete KHÔNG phát sinh điều kiện `WHERE is_deleted = false` trong SQL log.
- **SC-003**: 0% hồi quy (Zero Regressions) đối với toàn bộ các domain và model hiện tại (User, Meeting, Homework, PermissionRequest, BonusPoint, v.v.) đang dùng `id: int` và `is_deleted: bool`.
- **SC-004**: Thời gian tạo mới một module/domain entity mới với UUID và các mixin tùy chọn giảm ít nhất 50% thao tác thừa so với việc phải kế thừa các trường không mong muốn.

---

## Assumptions

- Các model hiện hữu trong hệ thống (như `User`, `Meeting`, `Homework`, `Violation`, `PermissionRequest`,...) tạm thời tiếp tục giữ nguyên kiểu khóa chính `id: int` và cơ chế `is_deleted` hiện tại để bảo toàn toàn vẹn dữ liệu và tránh việc migrate dữ liệu lớn đột ngột.
- Khóa ngoại `created_by` và `updated_by` trỏ tới bảng `users.id` vẫn là kiểu `int` (hoặc `int | None`), phù hợp với định danh của bảng `users` hiện thời.
- Việc hỗ trợ UUID sẽ áp dụng các chuẩn kiểu dữ liệu UUID nguyên bản của PostgreSQL (`UUID` native type) và kiểu `uuid.UUID` của Python 3.12.
