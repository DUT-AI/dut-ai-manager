# API Contract: Chi Tiết Trạng Thái Nộp Bài Tập Trên Manager

**Feature**: `008-detailed-exercise-history`  
**Date**: 2026-10-06  
**Status**: Active Contract

---

## 1. Endpoint Chi Tiết Trạng Thái Nộp Bài (`Manager -> Frontend`)

- **Method**: `GET`
- **URL**: `/api/v1/homeworks/{homework_id}/submission-status`
- **Authorization**: Bearer Token (Yêu cầu quyền xem bài tập)

---

## 2. Pydantic Models

```python
from datetime import datetime
from pydantic import BaseModel, Field


class ExerciseSummaryDTO(BaseModel):
    """Thông tin tóm tắt của một bài tập coding con."""
    exercise_id: str
    title: str
    order_index: int = 0


class StudentExerciseStatusDTO(BaseModel):
    """Trạng thái nộp bài của 1 học viên đối với 1 bài tập coding con."""
    exercise_id: str
    exercise_title: str
    is_submitted: bool = False
    is_passed: bool = False
    score: float | None = None
    attempt_number: int = 0
    submitted_at: datetime | None = None
    is_late: bool = False


class StudentHomeworkDetailDTO(BaseModel):
    """Tiến độ nộp bài tổng thể của 1 học viên được phân công."""
    user_id: int
    name: str
    avatar_url: str | None = None
    
    # Tiến độ Coding
    total_coding_required: int = 0
    total_coding_completed: int = 0
    coding_status: str                      # "COMPLETED" | "PARTIALLY_SUBMITTED" | "NOT_SUBMITTED"
    coding_is_late: bool = False
    coding_exercises: list[StudentExerciseStatusDTO] = Field(default_factory=list)
    
    # Tiến độ Game
    game_is_submitted: bool = False
    game_is_late: bool = False
    game_submitted_at: datetime | None = None
    game_score: float | None = None


class CategorySubmissionGroup(BaseModel):
    """Phân nhóm danh sách học viên theo trạng thái hoàn thành."""
    completed: list[StudentHomeworkDetailDTO] = Field(default_factory=list)
    partially_submitted: list[StudentHomeworkDetailDTO] = Field(default_factory=list)
    not_submitted: list[StudentHomeworkDetailDTO] = Field(default_factory=list)


class HomeworkDetailedSubmissionStatusResponse(BaseModel):
    """Response trả về toàn diện cho giao diện theo dõi tiến độ bài tập."""
    homework_id: int
    title: str
    deadline: datetime
    slug: str | None = None
    requires_coding: bool = True
    requires_game: bool = False
    
    # Danh sách bài tập con của bài học
    coding_exercises: list[ExerciseSummaryDTO] = Field(default_factory=list)
    
    # Phân nhóm trạng thái theo Coding
    coding: CategorySubmissionGroup
    
    # Phân nhóm trạng thái theo Game
    game: CategorySubmissionGroup
    
    # Danh sách toàn bộ học viên kèm ma trận tiến độ
    students: list[StudentHomeworkDetailDTO] = Field(default_factory=list)
```

---

## 3. JSON Response Example

```json
{
  "homework_id": 15,
  "title": "Deep Learning - Bài tập Tuần 4",
  "deadline": "2026-10-07T23:59:59+07:00",
  "slug": "batch-normalization",
  "requires_coding": true,
  "requires_game": true,
  "coding_exercises": [
    {
      "exercise_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "title": "Bài tập 1: Cài đặt BatchNorm2d Forward",
      "order_index": 1
    },
    {
      "exercise_id": "7a3ec51f-2e8d-4c59-b7aa-8c6f1d2e3b4a",
      "title": "Bài tập 2: Cài đặt BatchNorm2d Backward",
      "order_index": 2
    }
  ],
  "students": [
    {
      "user_id": 42,
      "name": "Nguyễn Văn A",
      "avatar_url": "https://example.com/avatars/user42.png",
      "total_coding_required": 2,
      "total_coding_completed": 2,
      "coding_status": "COMPLETED",
      "coding_is_late": false,
      "coding_exercises": [
        {
          "exercise_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
          "exercise_title": "Bài tập 1: Cài đặt BatchNorm2d Forward",
          "is_submitted": true,
          "is_passed": true,
          "score": 100.0,
          "attempt_number": 2,
          "submitted_at": "2026-10-06T14:30:00+07:00",
          "is_late": false
        },
        {
          "exercise_id": "7a3ec51f-2e8d-4c59-b7aa-8c6f1d2e3b4a",
          "exercise_title": "Bài tập 2: Cài đặt BatchNorm2d Backward",
          "is_submitted": true,
          "is_passed": true,
          "score": 95.0,
          "attempt_number": 1,
          "submitted_at": "2026-10-06T15:00:00+07:00",
          "is_late": false
        }
      ],
      "game_is_submitted": true,
      "game_is_late": false,
      "game_submitted_at": "2026-10-06T15:30:00+07:00",
      "game_score": 150.0
    },
    {
      "user_id": 43,
      "name": "Trần Thị B",
      "avatar_url": null,
      "total_coding_required": 2,
      "total_coding_completed": 1,
      "coding_status": "PARTIALLY_SUBMITTED",
      "coding_is_late": false,
      "coding_exercises": [
        {
          "exercise_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
          "exercise_title": "Bài tập 1: Cài đặt BatchNorm2d Forward",
          "is_submitted": true,
          "is_passed": true,
          "score": 80.0,
          "attempt_number": 1,
          "submitted_at": "2026-10-06T16:00:00+07:00",
          "is_late": false
        },
        {
          "exercise_id": "7a3ec51f-2e8d-4c59-b7aa-8c6f1d2e3b4a",
          "exercise_title": "Bài tập 2: Cài đặt BatchNorm2d Backward",
          "is_submitted": false,
          "is_passed": false,
          "score": null,
          "attempt_number": 0,
          "submitted_at": null,
          "is_late": false
        }
      ],
      "game_is_submitted": false,
      "game_is_late": false,
      "game_submitted_at": null,
      "game_score": null
    }
  ]
}
```
