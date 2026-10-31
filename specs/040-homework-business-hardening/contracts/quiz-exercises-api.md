# Contract: Quiz API - Lesson Exercises Integration

## 1. External Quiz Endpoint

```http
GET /api/v1/lessons/{lesson_slug}/exercises
Content-Type: application/json
```

### Success Response (200 OK)
```json
{
  "exercises": [
    {
      "id": "ex_binary_search_1",
      "lesson_id": "lesson_algo_01",
      "title": "Tìm kiếm nhị phân cơ bản",
      "description": "Cài đặt thuật toán tìm kiếm nhị phân...",
      "has_attachment": false
    },
    {
      "id": "ex_binary_search_2",
      "lesson_id": "lesson_algo_01",
      "title": "Tìm kiếm vị trí chèn",
      "description": "Áp dụng tìm kiếm nhị phân biến thể...",
      "has_attachment": true
    }
  ]
}
```

### Error Responses
- `404 Not Found`: Trả về `None` khi slug không tồn tại.
- `5xx / Network Error`: Client ném timeout hoặc trả về `[]`, trigger cơ chế fallback trong Use Case.

---

## 2. Permission Request Creation API (Postpone Endpoint Contract)

```http
POST /api/v1/permission-requests
Content-Type: application/json
```

### Request Body
```json
{
  "category": "POSTPONE",
  "reason": "Em bị sốt xuất huyết xin gia hạn nộp bài",
  "payload": {
    "homework_id": 12,
    "start_time": "2026-11-04T16:59:59Z"
  }
}
```

### Response Scenarios
- `200 OK`: Đơn được tạo thành công, deadline của học sinh trong `homework_assignees` được cập nhật thành `start_time`.
- `400 Bad Request`:
  - `{"detail": "Thời gian gia hạn mới phải ở tương lai"}` (nếu `start_time <= now`)
  - `{"detail": "Bài tập đã quá hạn, không thể tạo đơn xin hoãn"}` (nếu `current_deadline <= now`)
  - `{"detail": "Bạn đã hoàn thành bài tập này, không thể xin hoãn"}` (nếu `is_submitted == True`)
  - `{"detail": "Thời gian xin hoãn không được vượt quá 4 ngày so với deadline hiện tại"}` (nếu `start_time - current_deadline > 4 days`)
  - `{"detail": "Bạn không được phân công bài tập này"}` (nếu học sinh không có trong `homework_assignees`)
