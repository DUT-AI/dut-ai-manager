# Feature Specification: Đồng Nhất Kiến Trúc Phân Trang Giữa Frontend và Backend (Unified FE-BE Pagination)

**Feature Branch**: `009-unified-fe-be-pagination`

**Created**: 2026-10-10

**Status**: Clarified

**Input**: User request: "Hiện tại có 1 vấn đề là paging giữa FE và BE chưa đồng nhất, hãy suy nghĩ các cách để thiết kế cho tôi"

---

## Clarifications

### Session 2026-10-10
- Q: Cấu trúc phản hồi API (Response Envelope) cho các danh sách phân trang nên được chuẩn hoá theo mô hình nào? → A: Option A - Mở rộng Envelope gốc `ApiResponse`: `{ is_success, status_code, message, data: [...items], pagination: { page, page_size, total, total_pages, has_next } }`.
- Q: Chuẩn tham số truy vấn (Query Parameters) ở đầu vào của các API nên được quy định như thế nào? → A: Option B - Chuyển đổi cứng sang `page: int = 1, page_size: int = 20`, loại bỏ hoàn toàn `skip`/`limit` trên toàn hệ thống (BE, FE, Zalo Mini App).
- Q: Đối với các tính năng cần dữ liệu trọn vẹn (như Lịch Calendar theo tuần/tháng, Dropdown chọn thành viên/trainer), API nên được xử lý như thế nào? → A: Option A - Phân tách rõ ràng giữa endpoint quản trị danh sách (bắt buộc phân trang) và endpoint phục vụ Tra cứu/Lịch: Calendar nhận `start_date` & `end_date` lấy toàn bộ trong khoảng thời gian; Dropdown sử dụng endpoint `/options` riêng biệt (chỉ lấy id, name, avatar).
- Q: Cơ chế quản lý trạng thái phân trang (Pagination State Management) trên Frontend nên được tổ chức như thế nào? → A: Option A - Xây dựng Custom Hook chuẩn `useTablePagination` có đồng bộ trạng thái 2 chiều với URL Search Parameters (`useSearchParams`), tự động trả về Ant Design pagination props chuẩn theo Constitution Điều VIII.
- Q: Ở tầng Database / Repository của Backend, cơ chế tính toán `total` và cấu trúc dữ liệu trả về nên được thiết kế như thế nào? → A: Option A - Bổ sung phương thức dùng chung `get_paged(...)` trong `BaseRepository` trả về `tuple[list[TEntity], int]`, tự động bóc tách câu lệnh `COUNT` tối ưu (loại bỏ `ORDER BY` và eager joins) và câu lệnh `SELECT` phân trang.

---

## Bối Cảnh & Vấn Đề

Hiện tại trong hệ thống `DUT AI Manager`:
1. **Bất đồng nhất tham số Request**:
   - Backend nhiều nơi nhận `skip: int = 0, limit: int = 100` (như `/meetings`, `/violations`, `/homeworks`, `/billing`).
   - Một số nơi khác không nhận tham số phân trang mà trả về toàn bộ danh sách (`/users`).
   - Frontend và Ant Design `Table` lại hoạt động theo mô hình `page` (1-indexed: 1, 2, 3...) và `pageSize` (10, 20, 50, 100).
2. **Thiếu vắng Metadata Phân trang (Response Envelope)**:
   - Backend chỉ trả về `ApiResponse[list[T]]`, hoàn toàn không có `total`, `page`, `page_size`, `total_pages`. Database không thực thi `COUNT(*)` để đếm tổng số bản ghi khớp bộ lọc.
3. **Phân trang cục bộ giả lập ở Frontend (Client-side Pagination)**:
   - Frontend gán mảng `data` từ API vào `Table` với `pagination={{ pageSize: 10 }}`. Khi cơ sở dữ liệu có hơn 100 bản ghi, người dùng chỉ thấy tối đa 100 dòng đầu tiên; toàn bộ các trang từ 11 trở đi bị cắt cụt hoàn toàn.
4. **Vi phạm Constitution Điều VIII**:
   - Constitution quy định mọi bảng hiển thị dữ liệu kinh doanh PHẢI cấu hình phân trang rõ ràng với `defaultPageSize >= 20`, `pageSizeOptions: ['10', '20', '50', '100']`, `showSizeChanger: true`, và `showTotal`. Hiện tại hầu hết các bảng chỉ để mặc định 10 hoặc 15 mà không đồng bộ.

Tính năng này chuẩn hoá toàn diện kiến trúc phân trang 2 chiều giữa Frontend, Backend và Zalo Mini App.

---

## Kiến Trúc Thiết Kế Chi Tiết

### 1. Chuẩn Hóa Response Envelope (Backend & Shared DTO)
Mở rộng DTO `ApiResponse` trong `app.shared.application.response`:
```python
class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool

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

class ApiResponse(BaseModel, Generic[T]):
    is_success: bool
    status_code: int
    data: T | None = None
    message: str
    pagination: PaginationMeta | None = None
```
- Phía TypeScript Frontend (`frontend/src/types/api.types.ts` và `zalo-mini-app`):
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

### 2. Chuẩn Hóa Request Query Parameters
Xây dựng FastAPI Dependency `PaginationParams` trong `app.shared.application.pagination`:
```python
class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Trang hiện tại (1-based)")
    page_size: int = Field(default=20, ge=1, le=100, description="Kích thước trang (mặc định 20, tối đa 100)")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size
```
- Thay thế triệt để các tham số `skip` và `limit` trong toàn bộ Controllers, Use Cases và Repositories.

### 3. Phân Tách Ngữ Cảnh Chuyên Biệt
- **Danh sách quản trị chính**: Luôn áp dụng phân trang server-side bắt buộc (`page`, `page_size`).
- **Ngữ cảnh Lịch (Calendar)**: Endpoint `/meetings` hoặc `/meetings/calendar` khi nhận `start_date` và `end_date` sẽ trả về toàn bộ cuộc họp trong khoảng thời gian mà không phân trang (hoặc cho phép lấy toàn bộ trong khung tuần/tháng).
- **Ngữ cảnh Dropdown / Select Option**: Thêm endpoint gọn nhẹ `/users/options`, `/teams/options` chỉ trả về danh sách rút gọn (`id`, `name`, `avatar`) phục vụ các ô Select mà không bị giới hạn 20 dòng.

### 4. Tầng Database & BaseRepository (`get_paged`)
Bổ sung vào `BaseRepository`:
```python
def get_paged(
    self,
    query_support: QuerySupport,
    deleted: bool = False,
) -> tuple[list[TEntity], int]:
    # 1. Truy vấn COUNT tối ưu: Bỏ order_by và eager load
    count_query = select(func.count(self.model.id)).where(self.model.is_deleted == deleted)
    if query_support.filters:
        count_query = apply_filters_only(count_query, self.model, query_support.filters)
    total = self.session.scalar(count_query) or 0

    # 2. Truy vấn SELECT phân trang kèm eager loads & sorting
    select_query = select(self.model).where(self.model.is_deleted == deleted)
    select_query = apply_query_support(select_query, self.model, query_support)
    orms = self.session.scalars(select_query).unique().all()
    
    return [cast(TEntity, m.to_entity()) for m in orms], total
```

### 5. Frontend Custom Hook `useTablePagination`
Tạo tại `frontend/src/hooks/useTablePagination.ts`:
- Sử dụng `useSearchParams` của `react-router-dom`:
  - `page`: Đọc từ URL `?page=...`, fallback `1`.
  - `pageSize`: Đọc từ URL `?pageSize=...`, fallback `20`.
- Hàm `onChange(newPage, newPageSize)`: Cập nhật URL search params (hỗ trợ reset về trang 1 khi đổi bộ lọc search/filter).
- Trả về object `paginationProps` tương thích trực tiếp với Ant Design `Table.pagination`:
  - `current: page`
  - `pageSize: pageSize`
  - `total: totalRecords`
  - `showSizeChanger: true`
  - `pageSizeOptions: ['10', '20', '50', '100']`
  - `showTotal: (total, range) => \`${range[0]}-${range[1]} của ${total} bản ghi\``
  - `onChange: handlePaginationChange`

---

## User Scenarios & Acceptance Criteria

### User Story 1 - Phân trang Server-side chính xác cho Bảng Quản trị (Priority: P1)
Khi quản trị viên duyệt danh sách (Cuộc họp, Vi phạm, Bài tập, Học viên, Hóa đơn):
1. Bảng luôn hiển thị mặc định 20 dòng trên mỗi trang (`pageSize=20`).
2. Dòng hiển thị tổng số: `1-20 của 156 bản ghi`.
3. Khi chuyển sang trang 2, URL tự động cập nhật `?page=2&pageSize=20`, Backend nhận `page=2, page_size=20` và trả về đúng 20 bản ghi tiếp theo (từ bản ghi thứ 21 đến 40).
4. Khi người dùng F5 hoặc chia sẻ đường dẫn, trang 2 vẫn được mở chính xác.

### User Story 2 - Đổi kích thước trang (Page Size Changer) (Priority: P1)
Khi quản trị viên đổi hiển thị từ 20 sang 50 bản ghi:
1. URL cập nhật `?page=1&pageSize=50`.
2. Frontend gọi API với `page=1, page_size=50`.
3. Bảng hiển thị 50 bản ghi đầu tiên cùng tổng số trang được tính lại chính xác (`total_pages = 4`).

### User Story 3 - Bảo toàn hiển thị cho Lịch và Dropdown (Priority: P1)
1. Khi xem Lịch tuần tại `RobotActivityPage` hoặc `Calendar`: Toàn bộ các cuộc họp trong tuần hiển thị đầy đủ, không bị giới hạn cụt ở con số 20.
2. Khi mở Modal phân công/tạo bài tập: Ô Select thành viên/trainer tải từ `/users/options` hiển thị đầy đủ mọi học viên active trong hệ thống.

---

## Kế Hoạch Triển Khai

1. **Giai đoạn 1 (Backend Core)**:
   - Cập nhật `ApiResponse` với `pagination: PaginationMeta | None = None`.
   - Tạo `PaginationParams` dependency và cập nhật `QuerySupport` để nhận `page` & `page_size`.
   - Thêm `get_paged` vào `BaseRepository`.
2. **Giai đoạn 2 (Backend Endpoints Migration)**:
   - Refactor các controller danh sách: `/meetings`, `/violations`, `/homework`, `/users`, `/billing`, `/team`, `/rbac`.
   - Bổ sung endpoint `/users/options` cho dropdown.
3. **Giai đoạn 3 (Frontend Hook & Service Layer)**:
   - Thêm `PaginationMeta` vào `api.types.ts`.
   - Viết `useTablePagination` hook.
   - Cập nhật các service và query hooks để truyền `page` & `page_size`, đồng thời nhận cả `data` và `pagination`.
4. **Giai đoạn 4 (Frontend UI Refactor & Zalo Mini App)**:
   - Áp dụng `useTablePagination` vào các bảng Ant Design (`MeetingTable`, `ViolationTable`, `UserTable`, `HomeworkTable`, v.v.).
   - Kiểm tra và cập nhật `zalo-mini-app` tương thích với `page` & `page_size`.
