# Research & Architecture Decisions: Tách biệt Soft Delete và Hỗ trợ Khóa chính UUID cho Domain Model

**Feature**: `059-uuid-optional-soft-delete`  
**Date**: 2026-11-10  
**Status**: Completed  

---

## 1. Cơ chế sinh UUIDv7 trong Python 3.12 & Lưu trữ PostgreSQL

### Decision
- Xây dựng một module chuẩn hóa `app.shared.domain.uuid_utils` cung cấp hàm `uuid7() -> uuid.UUID` tuân thủ chuẩn **RFC 9562**.
- Hàm sử dụng `time.time_ns()` để lấy 48-bit timestamp (độ phân giải mili-giây) kết hợp với các byte ngẫu nhiên từ `os.urandom()` (hoặc `secrets.token_bytes()`), thiết lập 4-bit version `7` và 2-bit variant `2` (RFC 4122/9562).
- Về phía cơ sở dữ liệu PostgreSQL: Sử dụng kiểu dữ liệu native `UUID` của SQLAlchemy (`from sqlalchemy import UUID` với `as_uuid=True`), tự động map với kiểu `uuid.UUID` của Python và kiểu `UUID` nguyên bản của PostgreSQL. Default server-side có thể dùng hàm `gen_random_uuid()` hoặc client-side default qua `default=uuid7`.

### Rationale
- **Tối ưu B-Tree Index**: UUIDv4 có tính ngẫu nhiên 100%, khi chèn vào bảng dữ liệu lớn sẽ chèn ngẫu nhiên vào các node của B-Tree index, gây ra hiện tượng chia tách trang (page splits) và phân mảnh bộ nhớ (index fragmentation), làm chậm tốc độ ghi (INSERT) và giảm hiệu năng bộ nhớ đệm (cache hit ratio).
- **UUIDv7**: 48 bit đầu tiên là thời gian theo mili-giây, do đó các bản ghi mới chèn luôn có giá trị UUID lớn hơn các bản ghi trước đó, được chèn tuần tự vào đuôi của B-Tree index tương tự như Auto-Increment ID, nhưng vẫn giữ được đặc tính phân tán và không dự đoán được (ngẫu nhiên ở 74 bit còn lại).
- **Zero Third-party Dependencies**: Python 3.12 chưa tích hợp sẵn `uuid.uuid7()` (sẽ có trong Python 3.14). Việc triển khai hàm ~15 dòng chuẩn RFC 9562 bằng thư viện chuẩn `time`, `os`, `uuid` của Python giúp dự án không phụ thuộc vào thêm thư viện ngoài (như `uuid6` hay `uuid-utils`), đảm bảo tốc độ cao và ổn định tuyệt đối.

### Alternatives Considered
- **UUIDv4 (`uuid.uuid4()`)**: Đơn giản, sẵn có trong standard library. *Bị loại trừ* vì người dùng đã chỉ định chọn UUIDv7 và UUIDv4 gây suy giảm hiệu năng index ở các bảng lớn.
- **Thư viện ngoài `uuid6` / `uuid-utils`**: Đòi hỏi cài thêm package bên thứ ba trong `pyproject.toml`. *Bị loại trừ* vì thuật toán sinh UUIDv7 RFC 9562 rất ngắn gọn và không có lý do để thêm dependency rủi ro.

---

## 2. Tách biệt Composable Mixin cho SQLAlchemy ORM Models

### Decision
- Phân rã `SQLAlchemyTimestampMixin` hiện tại (vốn đang ôm đồm cả `created_at`, `updated_at`, `is_deleted`, `created_by`, `updated_by`) thành các Mixin chuyên biệt, đơn trách nhiệm (Single Responsibility):
  1. `SQLAlchemyTimestampMixin`: Chỉ chứa `created_at` và `updated_at` (chuẩn UTC timezone-aware).
  2. `SQLAlchemySoftDeleteMixin`: Chứa `is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)`.
  3. `SQLAlchemyAuditMixin`: Chứa `created_by: Mapped[int | None]` và `updated_by: Mapped[int | None]` trỏ tới `users.id`.
  4. `SQLAlchemyUuidPrimaryKeyMixin`: Chứa `id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)`.
  5. `SQLAlchemyIntPrimaryKeyMixin`: Chứa `id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)`.
  6. `SQLAlchemyFullAuditMixin`: Mixin kế thừa cả Timestamp, Audit và SoftDelete để tương thích 100% với các model cũ hiện tại.

### Rationale
- Các bảng mới trong tương lai có thể tự do lựa chọn kết hợp (Composition):
  - Model chỉ cần UUID + Timestamp (ví dụ: Log, Token, Transient session): `(SQLAlchemyUuidPrimaryKeyMixin, SQLAlchemyTimestampMixin, Base)`.
  - Model nghiệp vụ hoàn chỉnh cần UUID + Timestamp + Audit + Soft Delete: `(SQLAlchemyUuidPrimaryKeyMixin, SQLAlchemyTimestampMixin, SQLAlchemyAuditMixin, SQLAlchemySoftDeleteMixin, Base)`.
  - Không còn tình trạng mọi bảng đều bắt buộc phải có `is_deleted` và `int id`.
- **Zero Regression**: Đảm bảo toàn bộ các model cũ đang kế thừa `(SQLAlchemyTimestampMixin, Base)` vẫn tiếp tục hoạt động mà không cần refactor đồng loạt.

### Alternatives Considered
- **Tạo ORM Model cơ sở dạng Class kế thừa thay vì Mixin**: SQLAlchemy 2.0 hoạt động tốt nhất và linh hoạt nhất với Mapped Column Mixin. Việc dùng kế thừa nhiều tầng (Multi-table inheritance hoặc Concrete table inheritance) gây phức tạp schema và metadata của Alembic.

---

## 3. Kiến trúc Domain Entity trong Pydantic v2

### Decision
- Giữ nguyên `BaseEntity` hiện tại để bảo toàn tương thích ngược cho tất cả các domain hiện hữu (`User`, `Meeting`, `Homework`,...).
- Cung cấp kiến trúc Entity mới có tính module hóa:
  1. `BaseGenericEntity[TId](BaseModel)`: Chứa `id: TId | None`, `created_at`, `updated_at`.
  2. `BaseUuidEntity(BaseGenericEntity[UUID])`: Định nghĩa sẵn `id: UUID = Field(default_factory=uuid7)`.
  3. `SoftDeleteEntityMixin(BaseModel)`: Bổ sung `is_deleted: bool = False`.
  4. `AuditEntityMixin(BaseModel)`: Bổ sung `created_by: int | None = None` và `updated_by: int | None = None`.
- `BaseEntity` cũ được cấu trúc lại như một dạng alias/composition:
  `class BaseEntity(BaseGenericEntity[int], AuditEntityMixin, SoftDeleteEntityMixin)`.

### Rationale
- Đảm bảo tính nhất quán giữa ORM Model ở tầng Infrastructure và Domain Entity ở tầng Domain.
- Pydantic v2 `from_attributes=True` cho phép chuyển đổi mượt mà giữa ORM Model và Entity dù là kiểu `UUID` hay `int`.

---

## 4. Nâng cấp BaseRepository: Hỗ trợ linh hoạt Khóa chính & Xóa mềm/cứng

### Decision
- Giữ nguyên chữ ký generic 2 tham số `BaseRepository[TModel, TEntity]` để không phá vỡ các class Repository hiện hữu và Dishka Provider bindings.
- Các hàm truy vấn và thao tác trên ID (`get_by_id`, `delete`, `hard_delete`, `soft_delete`):
  - Nhận tham số `id: int | UUID | str`.
- **Xử lý Xóa mềm vs Xóa cứng**:
  - `soft_delete(id_or_entity)`: Kiểm tra `hasattr(model, "is_deleted")`. Nếu không có, ném ngoại lệ rõ ràng `NotImplementedError(f"Model {self.model.__name__} does not support soft delete")`. Nếu có, set `is_deleted = True` và flush.
  - `hard_delete(id_or_entity)`: Tìm bản ghi trong session và gọi `session.delete(model); session.flush()`. Áp dụng được cho cả model có và không có xóa mềm.
- **Tự động hóa lọc trong `get_all`, `get_paged`, `get_one`**:
  - Sử dụng kiểm tra `hasattr(self.model, "is_deleted")`.
  - Nếu model có trường `is_deleted`: thêm điều kiện lọc `where(self.model.is_deleted == deleted)`.
  - Nếu model không có trường `is_deleted`: KHÔNG thêm điều kiện lọc, cho phép query chạy trực tiếp mà không sinh lỗi `AttributeError`.

### Rationale
- Đáp ứng chính xác quyết định người dùng: phân tách rạch ròi `soft_delete()` và `hard_delete()`.
- Tự động hóa điều kiện query giúp các model không có `is_deleted` chạy mượt mà trên BaseRepository hiện tại mà không phải viết lại logic repository riêng.
