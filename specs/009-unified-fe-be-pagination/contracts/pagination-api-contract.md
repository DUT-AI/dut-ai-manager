# API Contract: Unified Pagination Contract

**Feature Branch**: `009-unified-fe-be-pagination` | **Date**: 2026-10-10

---

## 1. Request Query Contract

Tất cả các endpoint danh sách quản trị chấp nhận các query parameters sau:

| Parameter | Type | Required | Default | Constraints | Description |
|---|---|---|---|---|---|
| `page` | `integer` | No | `1` | `ge=1` | Số thứ tự trang hiện tại (bắt đầu từ 1) |
| `page_size` | `integer` | No | `20` | `ge=1, le=100` | Số lượng bản ghi tối đa trên một trang |

### Validation Errors
- Nếu client truyền `page=0` hoặc số âm: Trả về HTTP `422 Unprocessable Entity`.
- Nếu client truyền `page_size > 100`: Trả về HTTP `422 Unprocessable Entity` với thông báo lỗi rõ ràng.

---

## 2. Response Envelope Contract

Mọi endpoint danh sách phân trang trả về cấu trúc JSON sau:

```json
{
  "is_success": true,
  "status_code": 200,
  "message": "Fetched items successfully",
  "data": [
    {
      "id": 1,
      "name": "Bản ghi mẫu",
      "...": "..."
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 125,
    "total_pages": 7,
    "has_next": true
  }
}
```

### Trường hợp danh sách rỗng (`total = 0`):
```json
{
  "is_success": true,
  "status_code": 200,
  "message": "Fetched items successfully",
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 0,
    "total_pages": 0,
    "has_next": false
  }
}
```

---

## 3. Danh Sách Các Endpoints Nâng Cấp

### 3.1 Meetings (`/meetings`)
- `GET /meetings?page=1&page_size=20&deleted=false`
  - Quản lý danh sách các buổi họp (Server-side Pagination).
- `GET /meetings?start_date=2026-10-01&end_date=2026-10-07`
  - Lịch tuần/tháng (Calendar): Trả về toàn bộ cuộc họp trong khung ngày đã chỉ định, không áp dụng limit 20.

### 3.2 Users (`/users`)
- `GET /users?page=1&page_size=20&keyword=nguyen`
  - Danh sách người dùng trong User Management Table (Server-side Pagination).
- `GET /users/options`
  - Danh sách rút gọn (`id`, `name`, `email`, `avatar_url`) cho tất cả active users, phục vụ Select Trainer/Học viên trong Modal.

### 3.3 Violations (`/violations`)
- `GET /violations?page=1&page_size=20&month=10&year=2026`
  - Bảng danh sách vi phạm (Server-side Pagination).

### 3.4 Homeworks (`/homework`)
- `GET /homework?page=1&page_size=20&deleted=false`
  - Bảng danh sách bài tập (Server-side Pagination).

### 3.5 Billing / Invoices (`/billing/invoices`)
- `GET /billing/invoices?page=1&page_size=20`
  - Bảng danh sách hóa đơn (Server-side Pagination).

### 3.6 Teams (`/teams`)
- `GET /teams?page=1&page_size=20`
  - Bảng quản trị Team (Server-side Pagination).
- `GET /teams/options`
  - Danh sách rút gọn Team (`id`, `name`) cho ô Select.
