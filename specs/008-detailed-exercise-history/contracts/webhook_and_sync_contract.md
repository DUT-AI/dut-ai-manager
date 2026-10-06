# API Contract: Webhook & Sync Giữa Quiz Và Manager

**Feature**: `008-detailed-exercise-history`  
**Date**: 2026-10-06  
**Status**: Active Contract

---

## 1. Webhook Submission Payload (`Quiz -> Manager`)

- **Method**: `POST`
- **URL**: `{MANAGE_BASE_URL}/api/v1/homeworks/webhook/submission`
- **Headers**:
  - `Content-Type: application/json`
  - `X-Webhook-Secret: {MANAGE_WEBHOOK_SECRET}`

### Pydantic Model (Python)

```python
from datetime import datetime
from enum import StrEnum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SubmissionType(StrEnum):
    CODING = "CODING"
    GAME = "GAME"


class HomeworkSubmissionWebhookIn(BaseModel):
    """Payload schema nhận từ Quiz Webhook khi có sự kiện nộp bài hoặc hoàn thành game."""

    model_config = ConfigDict(populate_by_name=True)

    lesson_slug: str = Field(..., description="Slug định danh bài học trên Quiz")
    user_id: int = Field(..., description="ID học viên trong hệ thống Manage (user_id < 1,000,000)")
    type: SubmissionType = Field(..., description="Loại bài nộp: CODING hoặc GAME")
    submitted_at: datetime = Field(..., description="Mốc thời gian nộp bài")
    is_passed: bool = Field(default=True, description="Đánh giá đạt chuẩn bài tập")
    
    # Thông tin bài tập coding con (Chỉ có khi type == CODING)
    exercise_id: str | None = Field(default=None, description="UUID của bài tập coding con bên Quiz")
    exercise_title: str | None = Field(default=None, description="Tiêu đề bài tập coding con")
    submission_id: str | None = Field(default=None, description="UUID bản ghi bài nộp bên Quiz")
    attempt_number: int = Field(default=1, ge=1, description="Lần nộp thứ mấy của bài tập con")
    score: float | None = Field(default=None, ge=0.0, description="Điểm số đạt được (nếu có)")
    original_filename: str | None = Field(default=None, description="Tên file mã nguồn nộp")
    
    details: dict[str, Any] = Field(default_factory=dict, description="Dữ liệu chi tiết bổ sung")

    @field_validator("type", mode="before")
    @classmethod
    def parse_submission_type(cls, v: Any) -> SubmissionType:
        if isinstance(v, SubmissionType):
            return v
        if isinstance(v, str):
            val = v.strip().upper()
            if val in SubmissionType.__members__:
                return SubmissionType[val]
        raise ValueError(f"Invalid submission type: {v}. Must be CODING or GAME")
```

### JSON Request Example (Coding Exercise)

```json
{
  "lesson_slug": "batch-normalization",
  "user_id": 42,
  "type": "CODING",
  "submitted_at": "2026-10-06T14:30:00+07:00",
  "is_passed": true,
  "exercise_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "exercise_title": "Bài tập 1: Cài đặt BatchNorm2d Forward",
  "submission_id": "c8a6b2d1-9f3e-4b77-a8b2-5f8e6c1d4a3e",
  "attempt_number": 2,
  "score": 100.0,
  "original_filename": "batch_norm_forward.py",
  "details": {
    "test_cases_passed": 5,
    "total_test_cases": 5
  }
}
```

---

## 2. API Lấy Danh Sách Bài Tập Con Của Lesson (`Manager -> Quiz`)

- **Method**: `GET`
- **URL**: `{QUIZ_API_URL}/api/v1/lessons/{lesson_slug}/exercises`
- **Headers**: `Content-Type: application/json`

### Pydantic Models

```python
class ExerciseItemDTO(BaseModel):
    id: str                                 # UUID bài tập con
    lesson_id: str                          # UUID bài học
    title: str                              # Tên bài tập con
    description: str = ""                   # Mô tả đề bài
    created_at: datetime
    has_attachment: bool = False
    attachment_filename: str | None = None


class LessonExercisesMetadataResponse(BaseModel):
    lesson_slug: str
    lesson_name: str
    total_exercises: int
    exercises: list[ExerciseItemDTO]
```

### JSON Response Example

```json
{
  "data": {
    "lesson_slug": "batch-normalization",
    "lesson_name": "Batch Normalization Deep Dive",
    "total_exercises": 2,
    "exercises": [
      {
        "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
        "lesson_id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Bài tập 1: Cài đặt BatchNorm2d Forward",
        "description": "Thực hiện tính toán mean, variance và chuẩn hóa tensor.",
        "created_at": "2026-10-01T08:00:00+07:00",
        "has_attachment": true,
        "attachment_filename": "starter_code.zip"
      },
      {
        "id": "7a3ec51f-2e8d-4c59-b7aa-8c6f1d2e3b4a",
        "lesson_id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Bài tập 2: Cài đặt BatchNorm2d Backward Pass",
        "description": "Tính đạo hàm riêng đối với gamma, beta và đầu vào x.",
        "created_at": "2026-10-01T08:00:00+07:00",
        "has_attachment": false,
        "attachment_filename": null
      }
    ]
  }
}
```

---

## 3. API Đồng Bộ Lịch Sử Bài Nộp Chi Tiết (`Manager -> Quiz`)

- **Method**: `GET`
- **URL**: `{QUIZ_API_URL}/api/v1/homeworks/{lesson_slug}/submissions-for-sync`

### Pydantic Model

```python
class HomeworkSubmissionSyncItemDTO(BaseModel):
    submission_id: str
    exercise_id: str
    exercise_title: str
    user_id: int
    attempt_number: int
    original_filename: str
    submitted_at: datetime
    status: str
    is_pass: bool | None = True
    score: float | None = None
    score_details: list[dict[str, Any]] | None = None


class HomeworkSubmissionsSyncResponse(BaseModel):
    data: list[HomeworkSubmissionSyncItemDTO]
```
