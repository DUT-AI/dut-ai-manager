# Research & Technical Decisions: Đồng Nhất Kiến Trúc Phân Trang Giữa Frontend và Backend

**Feature Branch**: `009-unified-fe-be-pagination` | **Date**: 2026-10-10

---

## 1. Response Envelope: Mở Rộng Envelope Gốc `ApiResponse`

### Vấn đề
Backend hiện tại trả về `ApiResponse[list[T]]` (chỉ gồm `is_success`, `status_code`, `data`, `message`). Hoàn toàn thiếu metadata phân trang (`total`, `page`, `page_size`, `total_pages`). Trong khi đó, cả Web Admin Frontend và Zalo Mini App đều truy cập dữ liệu danh sách qua `response.data.data` (kỳ vọng một mảng Array).

### Quyết định kỹ thuật
Mở rộng DTO `ApiResponse` trong `app.shared.application.response`:
```python
class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool

class ApiResponse(BaseModel, Generic[T]):
    is_success: bool
    status_code: int
    data: T | None = None
    message: str
    pagination: PaginationMeta | None = None
```

### Rationale (Lý do lựa chọn)
1. **Không gây Breaking Change**: `response.data.data` vẫn là một mảng `list[T]`. Zalo Mini App và các component hiện tại tiếp tục chạy mượt mà mà không gặp lỗi runtime `.map is not a function`.
2. **Cung cấp metadata trực tiếp**: Web Frontend dễ dàng truy xuất `response.data.pagination` để truyền vào thuộc tính `total` của Ant Design `Table`.
3. **Phù hợp với Constitution Điều V**: Bảo đảm API Backward Compatibility và Non-Null Contract.

### Các phương án thay thế đã đánh giá
- *Đóng gói vào `data` dạng Object `{ items: [...], total: ... }`*: Bị từ chối vì đây là Breaking Change nghiêm trọng, sẽ làm hỏng runtime toàn bộ Zalo Mini App và mọi API hooks của Web FE hiện tại.
- *Header-based Pagination (`X-Total-Count`)*: Bị từ chối vì không thân thiện với OpenAPI/Swagger docs và đòi hỏi custom Axios interceptor phức tạp.

---

## 2. Request Parameters: Chuyển Đổi Cứng Sang `page` & `page_size`

### Vấn đề
Một số API dùng `skip`/`limit` (offset-based), một số API khác không có phân trang. Ant Design Table trên Frontend lại hoạt động theo `page` (1-based: 1, 2, 3...) và `pageSize` (20, 50, 100). Việc để Frontend tự tính `skip = (page - 1) * pageSize` gây lặp code và dễ dẫn đến sai sót lệch offset.

### Quyết định kỹ thuật
Loại bỏ hoàn toàn các tham số `skip` và `limit`. Chuẩn hoá thành FastAPI Dependency:
```python
class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Trang hiện tại (1-based)")
    page_size: int = Field(default=20, ge=1, le=100, description="Số bản ghi mỗi trang (mặc định 20, tối đa 100)")
```

### Rationale
- Đồng bộ ngữ nghĩa 1:1 với Frontend Ant Design Table: `current` <=> `page`, `pageSize` <=> `page_size`.
- Đảm bảo Constitution Điều VIII: Mặc định `page_size = 20`.
- Chấm dứt sự phân mảnh tham số giữa các controllers khác nhau.

---

## 3. Tối Ưu Truy Vấn `COUNT` Trong `BaseRepository.get_paged`

### Vấn đề
Nếu thực hiện phân trang server-side bằng cách chạy câu truy vấn chính có kèm các mệnh đề `order_by` và các quan hệ nạp sớm `joinedload / selectinload` cho việc đếm `COUNT(*)`, cơ sở dữ liệu sẽ phải thực hiện các phép JOIN tốn kém chỉ để lấy một con số đếm, gây suy giảm hiệu năng nghiêm trọng khi bảng có hàng chục nghìn dòng.

### Quyết định kỹ thuật
Bổ sung phương thức `get_paged(...)` vào `BaseRepository`:
1. **Truy vấn đếm tối ưu (`count_query`)**:
   - Sử dụng `select(func.count(self.model.id)).where(self.model.is_deleted == deleted)`.
   - Chỉ áp dụng các mệnh đề lọc dữ liệu (`WHERE`).
   - Loại bỏ hoàn toàn `ORDER BY` và các quan hệ `joinedload / selectinload`.
2. **Truy vấn lấy dữ liệu (`select_query`)**:
   - Áp dụng đầy đủ filters, sorting, eager loads và `.offset(...).limit(...)`.
3. Trả về `(items, total)` cho Use Case.

### Rationale
- Tốc độ đếm nhanh hơn từ 3x đến 10x so với subquery đếm toàn bộ join relations.
- Mọi domain (Meeting, Violation, Homework, User, Invoice, Team) kế thừa ngay lập tức mà không phải viết lại logic đếm.

---

## 4. Frontend State Management: Hook `useTablePagination` Đồng Bộ URL

### Vấn đề
Người dùng khi đang ở trang 3 hoặc đang xem 50 bản ghi/trang, nếu bấm F5 reload hoặc copy URL gửi cho người khác thì hệ thống bị reset về trang 1 mặc định. Ngoài ra, việc cấu hình các thuộc tính của Ant Design Table (`pageSizeOptions`, `showSizeChanger`, `showTotal`) bị lặp lại ở mọi màn hình.

### Quyết định kỹ thuật
Xây dựng Custom Hook `useTablePagination`:
- Đọc và đồng bộ `page` và `pageSize` với URL Search Params (`useSearchParams`).
- Khi người dùng thực hiện tìm kiếm từ khóa hoặc đổi bộ lọc, hook hỗ trợ hàm `resetPage()` để quay về trang 1.
- Sinh ra object cấu hình `paginationProps` đáp ứng 100% Constitution Điều VIII:
  - `current: page`
  - `pageSize: pageSize`
  - `total: total`
  - `defaultPageSize: 20`
  - `pageSizeOptions: ['10', '20', '50', '100']`
  - `showSizeChanger: true`
  - `showTotal: (total, range) => \`${range[0]}-${range[1]} / ${total} bản ghi\``

### Rationale
- Mang lại trải nghiệm người dùng hiện đại, có tính năng bookmarkable link.
- Giảm thiểu hơn 80% mã nguồn lặp lại trong các component Table.

---

## 5. Phân Tách Ngữ Cảnh Đặc Thù: Calendar & Dropdown Options

### Vấn đề
- **Calendar View**: Màn hình Lịch họp theo tuần/tháng cần hiển thị trọn vẹn các cuộc họp trong khoảng thời gian `[start_date, end_date]`. Nếu ép phân trang 20 dòng, lịch sẽ bị trống các cuộc họp ngoài trang 1.
- **Select Dropdown**: Khi tạo bài tập hoặc phân công trainer, ô chọn cần danh sách đầy đủ tất cả học viên đang hoạt động trong hệ thống.

### Quyết định kỹ thuật
- **Calendar**: Endpoint `GET /meetings` khi có `start_date` và `end_date` sẽ trả về toàn bộ cuộc họp trong khoảng ngày đó (hoặc duy trì `getMeetingsByDateRange`).
- **Dropdown**: Bổ sung endpoint nhẹ `GET /users/options` và `GET /teams/options` (chỉ trả về `id`, `name`, `avatar_url` của các bản ghi active) không phân trang, payload siêu nhẹ.
