# Data Model: Đồng Nhất Kiến Trúc Phân Trang Giữa Frontend và Backend

**Feature Branch**: `009-unified-fe-be-pagination` | **Date**: 2026-10-10

---

## 1. Backend Data Structures (Python / Pydantic V2)

### 1.1 `PaginationMeta` (Response Metadata DTO)
Được định nghĩa tại `app.shared.application.response`:

```python
from pydantic import BaseModel, Field

class PaginationMeta(BaseModel):
    page: int = Field(..., description="Trang hiện tại (1-indexed)")
    page_size: int = Field(..., description="Số lượng bản ghi trên một trang")
    total: int = Field(..., description="Tổng số bản ghi thỏa mãn điều kiện lọc")
    total_pages: int = Field(..., description="Tổng số trang có sẵn")
    has_next: bool = Field(..., description="Còn trang tiếp theo hay không")

    @classmethod
    def create(cls, page: int, page_size: int, total: int) -> "PaginationMeta":
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        has_next = page < total_pages
        return cls(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            has_next=has_next,
        )
```

### 1.2 `ApiResponse[T]` (Mở rộng Envelope gốc)
Được định nghĩa tại `app.shared.application.response`:

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    is_success: bool
    status_code: int
    data: T | None = None
    message: str
    pagination: PaginationMeta | None = None

    @classmethod
    def success(
        cls,
        data: T | None = None,
        message: str = "Success",
        status_code: int = 200,
        pagination: PaginationMeta | None = None,
    ) -> "ApiResponse[T]":
        return cls(
            is_success=True,
            status_code=status_code,
            data=data,
            message=message,
            pagination=pagination,
        )
```

### 1.3 `PaginationParams` (Request Query Dependency)
Được định nghĩa tại `app.shared.application.pagination`:

```python
from pydantic import BaseModel, Field

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Số thứ tự trang (bắt đầu từ 1)")
    page_size: int = Field(default=20, ge=1, le=100, description="Kích thước trang (mặc định 20, tối đa 100)")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size
```

### 1.4 `PagedResult[TEntity]` (Domain / Repository Layer Return Type)
Được định nghĩa tại `app.shared.domain.query_support`:

```python
from dataclasses import dataclass
from typing import Generic, TypeVar

TEntity = TypeVar("TEntity")

@dataclass(frozen=True, slots=True)
class PagedResult(Generic[TEntity]):
    items: list[TEntity]
    total: int
    page: int
    page_size: int
```

### 1.5 Option Models cho Dropdown (Lightweight Option DTOs)
Được định nghĩa tại `app.user.application.dtos` và `app.team.application.dtos`:

```python
class UserOptionDto(BaseModel):
    id: int
    name: str
    email: str
    avatar_url: str | None = None

class TeamOptionDto(BaseModel):
    id: int
    name: str
```

---

## 2. Frontend Data Structures (TypeScript)

### 2.1 `PaginationMeta` & `ApiResponse<T>`
Được định nghĩa tại `frontend/src/types/api.types.ts` và `zalo-mini-app/dut-manager/src/types/api.types.ts`:

```typescript
export interface PaginationMeta {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  has_next: boolean;
}

export interface ApiResponse<T> {
  is_success: boolean;
  status_code: number;
  data: T | null;
  message: string;
  pagination?: PaginationMeta | null;
}
```

### 2.2 `PaginationQueryParams`
Tham số truyền vào Axios Service:

```typescript
export interface PaginationQueryParams {
  page?: number;
  page_size?: number;
}
```

### 2.3 `TablePaginationConfig` Props (Ant Design Binding)
Kiểu dữ liệu sinh ra từ hook `useTablePagination`:

```typescript
export interface UseTablePaginationReturn {
  page: number;
  pageSize: number;
  setPage: (page: number) => void;
  setPageSize: (pageSize: number) => void;
  resetPage: () => void;
  paginationProps: {
    current: number;
    pageSize: number;
    total: number;
    defaultPageSize: number;
    pageSizeOptions: string[];
    showSizeChanger: boolean;
    showTotal: (total: number, range: [number, number]) => string;
    onChange: (page: number, pageSize: number) => void;
  };
}
```
