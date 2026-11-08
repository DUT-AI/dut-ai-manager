# Data Model & Schema Mapping: Clean & Strict Submission Details

**Feature**: `056-standardize-submission-metadata`  
**Date**: 2026-11-08

---

## 1. Pydantic Models (Backend - `app/homework/application/dtos.py`)

```python
from typing import Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.homework.domain.entity import SubmissionType

class CodingScoreDetail(BaseModel):
    criterion: str | None = None
    status: bool = True
    score: float | None = None
    message: str | None = None

class CodingSubmissionDetails(BaseModel):
    submission_id: str | None = None
    original_filename: str | None = None
    status: str | None = None
    score_details: list[dict[str, Any]] | list[CodingScoreDetail] | None = None
    source: str = "webhook"  # "webhook" | "manual_sync"

class GameSubmissionDetails(BaseModel):
    session_id: str | None = None
    final_score: float | None = None
    gold: int = 0
    total_questions: int = 0
    correct_count: int = 0
    attempt_count: int = 1
    source: str = "webhook"  # "webhook" | "manual_sync"

class HomeworkSubmissionDetailResponse(BaseModel):
    id: int
    homework_id: int
    user_id: int
    submission_type: SubmissionType
    exercise_id: str | None = None
    exercise_title: str | None = None
    score: float | None = None
    attempt_number: int = 1
    submitted_at: datetime | None = None
    is_passed: bool = True
    # Clean & Strict: Xóa dict[str, Any], dùng trực tiếp Union có kiểu
    details: CodingSubmissionDetails | GameSubmissionDetails
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def parse_typed_details(cls, data: Any) -> Any:
        if isinstance(data, dict):
            raw_details = data.get("details") or {}
            sub_type = str(data.get("submission_type", "")).upper()
            if not isinstance(raw_details, (CodingSubmissionDetails, GameSubmissionDetails)):
                if sub_type == "GAME":
                    data["details"] = GameSubmissionDetails(**raw_details)
                else:
                    data["details"] = CodingSubmissionDetails(**raw_details)
        elif hasattr(data, "submission_type") and hasattr(data, "details"):
            sub_type = getattr(data.submission_type, "value", str(data.submission_type)).upper()
            raw_details = data.details or {}
            if not isinstance(raw_details, (CodingSubmissionDetails, GameSubmissionDetails)):
                if sub_type == "GAME":
                    data.details = GameSubmissionDetails(**raw_details)
                else:
                    data.details = CodingSubmissionDetails(**raw_details)
        return data
```

---

## 2. Generated TypeScript Types (Frontend - `api.generated.d.ts`)

Sau khi chạy `npm run generate:api`:

```typescript
export type HomeworkSubmissionDetailResponse = Schema<'HomeworkSubmissionDetailResponse'>;

// details sẽ có type chuẩn xác:
// details: components["schemas"]["CodingSubmissionDetails"] | components["schemas"]["GameSubmissionDetails"];
```
