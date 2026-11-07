# Contract: Homework Detail API (`GET /homeworks/{id}`)

## Endpoint
- **Method**: `GET`
- **Path**: `/homeworks/{homework_id}`
- **Authentication**: Bearer Token
- **Permission**: `HOMEWORK:READ`

## Response Body (`ApiResponse[HomeworkResponseDetail]`)
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "id": 79,
    "title": "Gen2: Đại số tuyến tính",
    "deadline": "2026-11-01T09:00:00Z",
    "link": "https://quiz.ai-center.edu.vn/courses/...",
    "slug": "dai-so-tuyen-tinh",
    "requires_coding": true,
    "requires_game": true,
    "assignee_ids": [59, 60, 61],
    "coding_exercises": [
      {
        "exercise_id": "201571b1-f668-4152-b91b-79c74bb1b485",
        "title": "Bài tập đại số tuyến tính hơi cơ bản",
        "order_index": 1,
        "completed_count": 37,
        "total_assigned": 40,
        "completion_rate": 92.5
      },
      {
        "exercise_id": "7761d9b8-775e-46ac-b87d-349f9d032588",
        "title": "Bài tập đại số tuyến tính",
        "order_index": 2,
        "completed_count": 35,
        "total_assigned": 40,
        "completion_rate": 87.5
      }
    ],
    "created_at": "2026-10-25T08:00:00Z",
    "updated_at": "2026-10-31T08:00:00Z",
    "created_by": 1
  }
}
```
