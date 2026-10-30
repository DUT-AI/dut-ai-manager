# Feature Specification: Generic Payload Entity & Strategy Pattern for Permission Requests

**Feature Branch**: `036-refactor-permission-strategy-pattern`  
**Created**: 2026-10-31  
**Status**: Draft  

## 1. Problem Statement
Hiện tại, mô hình lưu trữ và xử lý đơn xin phép trong `dut-ai-manager` đang gặp 2 vấn đề lớn:
1. **Vi phạm Database Normalization & Single Responsibility**:
   - Bảng `permission_requests` chứa các cột chuyên biệt rải rác: `homework_id`, `meeting_id`, `old_meeting_id`, `start_time`.
   - Các cột này bị `NULL` chéo nhau tùy loại đơn, dẫn đến mỗi lần thêm 1 loại đơn xin phép mới là phải chạy migration sửa bảng DB.
2. **Thiếu Type Safety hoặc Code Smell `Any`**:
   - Sử dụng `dict[str, Any]` sẽ làm mất hoàn toàn Type Hint, IDE autocomplete, dễ sinh lỗi chính tả key và dữ liệu rác.
3. **Vi phạm Open/Closed Principle (OCP)**:
   - Các use cases (`CreatePermissionRequestUseCase`, `DeletePermissionRequestUseCase`) dùng chuỗi `if-else` dài kiểm tra `category`, kéo theo nhiều dependency không cần thiết.

Người dùng yêu cầu: **Áp dụng Cách 2 - Generic Entity với TypeVar `PermissionRequest[TPayload]` kết hợp Strategy Pattern & JSONB Storage** để đạt sự chuyên nghiệp, type-safe 100% và đi đường dài.

---

## 2. Thiết kế Kiến trúc Chuẩn (Target Architecture)

### 2.1. Typed Domain Value Objects (Payloads)
Mỗi loại đơn sở hữu một Pydantic Value Object cụ thể, kế thừa `BasePermissionPayload`:

```python
class BasePermissionPayload(BaseModel):
    category: RequestCategory

class AbsencePayload(BasePermissionPayload):
    category: Literal[RequestCategory.ABSENCE] = RequestCategory.ABSENCE
    meeting_id: int

class LatePayload(BasePermissionPayload):
    category: Literal[RequestCategory.LATE] = RequestCategory.LATE
    meeting_id: int
    expected_arrival_time: UtcDateTime

class PostponePayload(BasePermissionPayload):
    category: Literal[RequestCategory.POSTPONE] = RequestCategory.POSTPONE
    homework_id: int
    extended_deadline: UtcDateTime

class OtherPayload(BasePermissionPayload):
    category: Literal[RequestCategory.OTHER] = RequestCategory.OTHER

class ChangeMeetingPayload(BasePermissionPayload):
    category: Literal[RequestCategory.CHANGE_MEETING] = RequestCategory.CHANGE_MEETING
    meeting_id: int
    old_meeting_id: int | None = None
```

### 2.2. Generic Domain Entity `PermissionRequest[TPayload]`
```python
TPayload = TypeVar("TPayload", bound=BasePermissionPayload)

class PermissionRequest(BaseEntity, Generic[TPayload]):
    user_id: int | None
    note: str
    payload: TPayload
    creator: UserRef | None = None
    updater: UserRef | None = None

    @property
    def category(self) -> RequestCategory:
        return self.payload.category
```

### 2.3. Generic Strategy Interface `PermissionStrategy[TPayload]`
```python
class PermissionStrategy(Generic[TPayload], ABC):
    category: RequestCategory

    @abstractmethod
    def validate(self, request: PermissionRequest[TPayload]) -> None:
        """Kiểm tra tính hợp lệ của đơn theo nghiệp vụ của loại đó."""
        ...

    @abstractmethod
    def on_created(self, request: PermissionRequest[TPayload], user_id: int) -> None:
        """Tác động trạng thái (side-effects) sau khi đơn được lưu thành công."""
        ...

    @abstractmethod
    def on_deleted(self, request: PermissionRequest[TPayload], user_id: int) -> None:
        """Khôi phục trạng thái khi đơn bị xóa/hủy."""
        ...
```

### 2.4. Storage (Database Layer)
Bảng `permission_requests`:
- Cột `payload JSONB NOT NULL DEFAULT '{}'::jsonb`: Lưu trữ toàn bộ dữ liệu của `TPayload`.
- Vẫn giữ các cột `homework_id`, `meeting_id`, `start_time` (với migration an toàn / hybrid mapping) để đảm bảo không làm gián đoạn frontend hiện tại và lịch sử dữ liệu.

---

## 3. Scope of Work
1. **Domain Layer**:
   - `backend/app/permission_request/domain/payloads.py`: Khai báo các Payload Value Objects.
   - `backend/app/permission_request/domain/entity.py`: Chuyển sang Generic Entity `PermissionRequest[TPayload]`.
2. **Strategy Handlers**:
   - `backend/app/permission_request/application/strategies/base.py`: Abstract `PermissionStrategy[TPayload]`.
   - `absence_strategy.py`: `AbsenceStrategy(PermissionStrategy[AbsencePayload])`.
   - `late_strategy.py`: `LateStrategy(PermissionStrategy[LatePayload])`.
   - `postpone_strategy.py`: `PostponeStrategy(PermissionStrategy[PostponePayload])`.
   - `other_strategy.py`: `OtherStrategy(PermissionStrategy[OtherPayload])`.
   - `registry.py`: `PermissionStrategyRegistry`.
3. **Application Use Cases**:
   - `CreatePermissionRequestUseCase`: Nhận `PermissionRequest[AnyPayload]`, ủy quyền cho `strategy = registry.get(category)`.
   - `DeletePermissionRequestUseCase`: Ủy quyền dọn dẹp cho `strategy.on_deleted(...)`.
4. **Infrastructure Layer**:
   - `model.py` & `repository.py`: Bổ sung mapping `payload JSONB` hai chiều giữa ORM Model và Generic Entity.
   - Migration Alembic: Thêm cột `payload JSONB` và populate dữ liệu cũ vào `payload`.
5. **Presentation Layer**:
   - Cung cấp getter compatibility trên DTO response (`start_time`, `meeting_id`, `homework_id`) để **Frontend chạy mượt mà 100% không bị ảnh hưởng**.

## 4. Success Criteria
- 100% Type-Safe: Không dùng `dict[str, Any]` trong Domain Model.
- Strategy Pattern hoàn chỉnh: Thêm loại đơn mới không cần sửa use case.
- Zero Downtime / Backward Compatible cho Frontend.
- Toàn bộ 168 unit tests tiếp tục pass 100%.
