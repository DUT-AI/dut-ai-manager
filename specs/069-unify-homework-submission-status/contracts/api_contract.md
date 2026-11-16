# API Contract: Unified Homework Submission Status

**Feature**: `069-unify-homework-submission-status`  
**Date**: 2026-11-15  

## 1. Endpoints

### 1.1 `GET /api/v1/homework/my-homeworks`
Lấy danh sách bài tập được phân công của học viên đang đăng nhập kèm trạng thái hoàn thành chuẩn hóa.

* **Query Parameters**:
  * `page` (int, default: 1)
  * `page_size` (int, default: 20)
* **Response Body** (`ApiResponse[PagedResponse[HomeworkResponse]]`):
```json
{
  "is_success": true,
  "data": {
    "items": [
      {
        "id": 105,
        "title": "Gen2: Bài tập Đại số tuyến tính",
        "deadline": "2026-11-20T17:00:00Z",
        "link": "https://quiz.example.com/lesson/dai-so-tuyen-tinh",
        "slug": "dai-so-tuyen-tinh",
        "requires_coding": true,
        "requires_game": true,
        "is_submitted": false,
        "is_overdue": false,
        "has_coding": true,
        "coding_submitted": false,
        "has_game": true,
        "game_submitted": true,
        "coding_status": "PARTIALLY_SUBMITTED",
        "total_coding_required": 2,
        "total_coding_completed": 1,
        "uncompleted_items": [
          "Còn 1/2 bài tập Coding"
        ],
        "created_at": "2026-11-01T08:00:00Z",
        "updated_at": "2026-11-01T08:00:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  },
  "message": "Success"
}
```

---

### 1.2 `GET /api/v1/homework/unsubmitted`
Lấy danh sách các bài tập chưa hoàn thành (bao gồm cả các bài làm dở) của học viên.

* **Query Parameters**:
  * `user_id` (int, optional - mặc định là user hiện tại)
* **Response Body** (`ApiResponse[list[HomeworkResponse]]`):
```json
{
  "is_success": true,
  "data": [
    {
      "id": 105,
      "title": "Gen2: Bài tập Đại số tuyến tính",
      "deadline": "2026-11-20T17:00:00Z",
      "requires_coding": true,
      "requires_game": true,
      "is_submitted": false,
      "coding_status": "PARTIALLY_SUBMITTED",
      "total_coding_required": 2,
      "total_coding_completed": 1,
      "uncompleted_items": [
        "Còn 1/2 bài tập Coding"
      ]
    }
  ],
  "message": "Success"
}
```

---

### 1.3 `GET /api/v1/homework/reports/unsubmitted`
Báo cáo thống kê số bài chưa hoàn thành của tất cả học viên (dành cho Admin/Leader).

* **Response Body** (`ApiResponse[list[HomeworkReportResponse]]`):
```json
{
  "is_success": true,
  "data": [
    {
      "user_id": 12,
      "owner": {
        "id": 12,
        "name": "Đỗ Quảng Giác",
        "email": "giac.do@example.com",
        "avatar_url": null
      },
      "unsubmitted_count": 1
    }
  ],
  "message": "Success"
}
```
*Học viên mới hoàn thành 1/2 bài con sẽ được tính vào `unsubmitted_count` (không bị coi là đã nộp).*
