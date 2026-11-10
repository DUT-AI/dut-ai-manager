# Data Model & Contracts: Tách biệt Soft Delete và Hỗ trợ Khóa chính UUID cho Domain Model

**Feature**: `059-uuid-optional-soft-delete`  
**Date**: 2026-11-10  
**Status**: Completed  

---

## 1. Domain Entities (`backend/app/shared/domain/`)

### 1.1. Module sinh UUIDv7: `backend/app/shared/domain/uuid_utils.py`

```python
import os
import time
import uuid

def uuid7() -> uuid.UUID:
    """
    Sinh mã định danh UUIDv7 chuẩn RFC 9562 (Time-ordered UUID).
    - 48 bits: Unix timestamp tính theo milliseconds.
    - 4 bits: Version 7 (0b0111).
    - 12 bits: rand_a (ngẫu nhiên).
    - 2 bits: Variant 2 (0b10, RFC 4122/9562).
    - 62 bits: rand_b (ngẫu nhiên).
    """
    ns = time.time_ns()
    timestamp_ms = ns // 1_000_000
    time_high = timestamp_ms & 0xFFFFFFFFFFFF
    rand_bytes = os.urandom(10)
    rand_a = int.from_bytes(rand_bytes[:2], "big") & 0x0FFF
    rand_b = int.from_bytes(rand_bytes[2:], "big") & 0x3FFFFFFFFFFFFFFF

    uuid_int = (time_high << 80) | (0x7 << 76) | (rand_a << 64) | (0x2 << 62) | rand_b
    return uuid.UUID(int=uuid_int)
```

### 1.2. Phân cấp Base Domain Entity: `backend/app/shared/domain/base_entity.py`

```python
from datetime import UTC, datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from app.shared.domain.uuid_utils import uuid7

TId = TypeVar("TId")

class BaseGenericEntity(BaseModel, Generic[TId]):
    """Base domain entity linh hoạt kiểu khóa chính TId, NO ORM dependency."""
    model_config = ConfigDict(from_attributes=True)

    id: TId | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

class SoftDeleteEntityMixin(BaseModel):
    """Mixin tùy chọn bổ sung trường xóa mềm cho Domain Entity."""
    is_deleted: bool = False

class AuditEntityMixin(BaseModel):
    """Mixin tùy chọn bổ sung thông tin người tạo/cập nhật."""
    created_by: int | None = None
    updated_by: int | None = None

class BaseUuidEntity(BaseGenericEntity[UUID]):
    """Base entity sử dụng khóa chính UUIDv7 mặc định cho các domain mới."""
    id: UUID = Field(default_factory=uuid7)

class BaseEntity(BaseGenericEntity[int], AuditEntityMixin, SoftDeleteEntityMixin):
    """
    Base entity tương thích ngược 100% cho các domain hiện hữu:
    Có id: int | None, created_at, updated_at, created_by, updated_by, is_deleted.
    """
    pass
```

---

## 2. Infrastructure ORM Mixins (`backend/app/shared/infrastructure/base_model.py`)

### 2.1. Phân rã Composable Mixins

```python
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, func
from sqlalchemy import UUID as SQLAlchemyUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.context import get_current_user_id
from app.shared.domain.uuid_utils import uuid7

class Base(DeclarativeBase):
    """Lớp cơ sở cho toàn bộ SQLAlchemy 2.0 ORM models."""
    pass

class SQLAlchemyUuidPrimaryKeyMixin:
    """Mixin khóa chính UUIDv7 cho các model mới."""
    id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

class SQLAlchemyIntPrimaryKeyMixin:
    """Mixin khóa chính Integer Auto-increment cho các model cũ."""
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

class SQLAlchemyTimestampMixin:
    """Mixin thuần túy cho thời gian tạo và cập nhật UTC."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
    )

class SQLAlchemySoftDeleteMixin:
    """Mixin độc lập cho cờ xóa mềm is_deleted."""
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

class SQLAlchemyAuditMixin:
    """Mixin độc lập cho người tạo và người cập nhật."""
    created_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), default=get_current_user_id, nullable=True
    )
    updated_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        default=get_current_user_id,
        onupdate=get_current_user_id,
        nullable=True,
    )

class SQLAlchemyFullAuditMixin(
    SQLAlchemyTimestampMixin,
    SQLAlchemySoftDeleteMixin,
    SQLAlchemyAuditMixin,
):
    """
    Mixin tương thích ngược hoàn toàn cho các model hiện hữu kế thừa Timestamp + SoftDelete + Audit.
    Subclasses chỉ cần implement from_entity() và to_entity().
    """
    @classmethod
    def from_entity(cls, entity: Any) -> Any:
        raise NotImplementedError("Subclasses must implement from_entity")

    def to_entity(self) -> Any:
        raise NotImplementedError("Subclasses must implement to_entity")
```

---

## 3. BaseRepository Contract (`backend/app/shared/infrastructure/base_repository.py`)

### 3.1. Chữ ký phương thức

```python
class BaseRepository[TModel, TEntity]:
    def __init__(self, session: Session, model: type[TModel]): ...

    def add(self, entity: TEntity) -> TEntity: ...

    def get_by_id(self, id: int | UUID | str) -> TEntity | None:
        """
        Lấy model theo ID (int hoặc UUID hoặc str UUID).
        Nếu model có xóa mềm và is_deleted == True, trả về None.
        """

    def get_one(
        self,
        query_support: QuerySupport,
        deleted: bool = False,
    ) -> TEntity | None:
        """
        Truy vấn 1 bản ghi.
        Chỉ sinh 'where(model.is_deleted == deleted)' nếu model có trường is_deleted.
        """

    def get_all(
        self,
        query_support: QuerySupport | None = None,
        deleted: bool = False,
    ) -> list[TEntity]:
        """
        Lấy toàn bộ bản ghi.
        Tự động bỏ qua lọc xóa mềm nếu model không có is_deleted.
        """

    def get_paged(
        self,
        query_support: QuerySupport | None = None,
        deleted: bool = False,
    ) -> tuple[list[TEntity], int]:
        """
        Lấy danh sách phân trang và tổng số bản ghi.
        Tự động bỏ qua lọc xóa mềm nếu model không có is_deleted.
        """

    def soft_delete(self, id_or_entity: int | UUID | str | TEntity) -> bool:
        """
        Đánh dấu xóa mềm bản ghi.
        RAISE NotImplementedError nếu model không hỗ trợ is_deleted.
        """

    def hard_delete(self, id_or_entity: int | UUID | str | TEntity) -> bool:
        """
        Xóa vật lý vĩnh viễn bản ghi khỏi cơ sở dữ liệu.
        Áp dụng cho cả model có và không có xóa mềm.
        """
```

---

## 4. Bảng Tra cứu Cách Sử Dụng cho Module Mới

| Loại Model | Domain Entity kế thừa | ORM Model kế thừa | Hành vi Xóa |
|---|---|---|---|
| **Dữ liệu Tạm / Log / Token** | `BaseUuidEntity` | `SQLAlchemyUuidPrimaryKeyMixin`, `SQLAlchemyTimestampMixin`, `Base` | Chỉ dùng `hard_delete()` |
| **Dữ liệu Nghiệp vụ Không Xóa mềm** | `BaseUuidEntity`, `AuditEntityMixin` | `SQLAlchemyUuidPrimaryKeyMixin`, `SQLAlchemyTimestampMixin`, `SQLAlchemyAuditMixin`, `Base` | Chỉ dùng `hard_delete()` |
| **Dữ liệu Nghiệp vụ Có Xóa mềm** | `BaseUuidEntity`, `AuditEntityMixin`, `SoftDeleteEntityMixin` | `SQLAlchemyUuidPrimaryKeyMixin`, `SQLAlchemyTimestampMixin`, `SQLAlchemyAuditMixin`, `SQLAlchemySoftDeleteMixin`, `Base` | Hỗ trợ cả `soft_delete()` và `hard_delete()` |
| **Model Cũ (Legacy)** | `BaseEntity` | `SQLAlchemyTimestampMixin` (hoặc `SQLAlchemyFullAuditMixin`), `Base` | Hỗ trợ cả `soft_delete()` và `hard_delete()` |
