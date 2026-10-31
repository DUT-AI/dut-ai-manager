# Contract: Sync Homework API Endpoint

**Endpoint**: `POST /api/v1/homeworks/{homework_id}/sync`  
**Quyền hạn**: `HomeworkPermission.UPDATE`  

---

## 1. Request
- **Path Parameter**:
  - `homework_id` (`int`): ID của bài tập cần đồng bộ.
- **Headers**:
  - `Authorization`: `Bearer <token>`

---

## 2. Response

### Status: 200 OK (Thành công)
```json
{
  "is_success": true,
  "code": 200,
  "data": {
    "homework_id": 105,
    "title": "Machine Learning: Decision Trees",
    "requires_coding": true,
    "requires_game": true,
    "coding_exercises_count": 3,
    "game_questions_count": 15,
    "synced_coding_count": 2,
    "updated_coding_count": 5,
    "synced_game_count": 1,
    "updated_game_count": 4,
    "message": "Đồng bộ thành công: Nhận diện 3 bài tập coding, 15 câu hỏi game. Đã kéo 2 bài nộp coding mới, 1 lượt game mới."
  },
  "message": null,
  "errors": null
}
```

### Status: 404 Not Found (Không tìm thấy bài tập)
```json
{
  "is_success": false,
  "code": 404,
  "data": null,
  "message": "Không tìm thấy bài tập để đồng bộ",
  "errors": null
}
```
