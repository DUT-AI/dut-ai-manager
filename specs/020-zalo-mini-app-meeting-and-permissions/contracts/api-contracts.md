# API Contracts: Zalo Mini App Meeting & Permissions

## 1. Meeting Detail API
- **Endpoint**: `GET /api/v1/meetings/{id}`
- **Response**:
```json
{
  "is_success": true,
  "data": {
    "id": 101,
    "title": "Sinh hoạt chuyên môn Tuần 42",
    "description": "Thảo luận về Zalo Mini App và AI Integration",
    "start_time": "2026-10-25T08:00:00Z",
    "end_time": "2026-10-25T11:00:00Z",
    "location": "Phòng Lab A302",
    "meeting_url": "https://meet.google.com/abc-xyz",
    "max_participants": 30,
    "require_check_in": true,
    "enable_evaluation": true,
    "participants": [
      {
        "id": 501,
        "meeting_id": 101,
        "user_id": 12,
        "role": "trainee",
        "status": "JOINED",
        "check_in_time": "2026-10-25T08:05:00Z",
        "user": {
          "id": 12,
          "name": "Nguyễn Văn A",
          "avatar_url": null
        }
      }
    ]
  }
}
```

## 2. Participant Status Update API
- **Endpoint**: `PUT /api/v1/meetings/{meeting_id}/participants/{user_id}/status`
- **Request Body**:
```json
{
  "status": "JOINED",
  "note": "Host điểm danh thủ công tại phòng"
}
```

## 3. Meeting Trainee Evaluation API
- **Endpoint**: `POST /api/v1/meetings/{meeting_id}/evaluations/trainee`
- **Request Body**:
```json
{
  "trainee_id": 12,
  "criteria": [
    {
      "criteria_name": "Kỹ năng chuyên môn",
      "score": 9,
      "comment": "Nắm vững kiến thức"
    },
    {
      "criteria_name": "Thái độ tham gia",
      "score": 10,
      "comment": "Tích cực thảo luận"
    }
  ],
  "general_comment": "Hoàn thành xuất sắc buổi học"
}
```

## 4. Permission Request Filter API
- **Endpoint**: `GET /api/v1/permission-requests`
- **Query Params**:
  - `page`: number (default 1)
  - `page_size`: number (default 20)
  - `category`: string (optional, e.g. `CHANGE_MEETING`)
  - `only_mine`: boolean (optional)
