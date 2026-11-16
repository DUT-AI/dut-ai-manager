# Phase 1 Data Model: Thống nhất Trạng thái Hoàn thành Bài tập

**Feature**: `069-unify-homework-submission-status`  
**Date**: 2026-11-15  

## 1. Value Objects

### `SubmissionEvaluation` (`backend/app/homework/domain/value_objects.py`)
Mở rộng đối tượng giá trị phản ánh kết quả đánh giá nộp bài:

```python
class SubmissionEvaluation(BaseModel):
    is_submitted: bool
    is_overdue: bool
    coding_submitted: bool
    game_submitted: bool
    uncompleted_items: list[str]
    # Bổ sung các trường tiến độ mới
    coding_status: str = "NOT_SUBMITTED"  # "COMPLETED" | "PARTIALLY_SUBMITTED" | "NOT_SUBMITTED"
    total_coding_required: int = 0
    total_coding_completed: int = 0
```

---

## 2. Domain Entity

### `Homework` (`backend/app/homework/domain/entity.py`)
Mở rộng phương thức `evaluate_submissions`:

```python
class Homework(BaseAuditEntity):
    id: int | None
    title: str
    link: str | None = None
    slug: str | None = None
    requires_coding: bool = True
    requires_game: bool = False

    def evaluate_submissions(
        self,
        submissions: list["HomeworkSubmission"],
        deadline: datetime | None = None,
        reference_time: datetime | None = None,
        required_exercise_ids: set[str] | None = None,
    ) -> SubmissionEvaluation:
        """
        Aggregate Root đối chiếu danh sách bài nộp với yêu cầu của đề bài.
        Hỗ trợ kiểm tra nghiêm ngặt danh sách bài tập con required_exercise_ids.
        """
```

### Quy tắc chuyển đổi trạng thái (State Transition Logic):

| Điều kiện Coding | Điều kiện Game | Trạng thái Coding | Trạng thái Game | Trạng thái Chung `is_submitted` |
|---|---|---|---|---|
| Không yêu cầu Coding | Yêu cầu Game, đã hoàn thành | N/A | COMPLETED | `True` (Đã hoàn thành) |
| Yêu cầu Coding, hoàn thành đủ $N/N$ bài con | Không yêu cầu Game | COMPLETED | N/A | `True` (Đã hoàn thành) |
| Yêu cầu Coding, hoàn thành đủ $N/N$ bài con | Yêu cầu Game, đã hoàn thành | COMPLETED | COMPLETED | `True` (Đã hoàn thành) |
| Yêu cầu Coding, chỉ hoàn thành $K/N$ bài con ($K < N$) | Bất kỳ | PARTIALLY_SUBMITTED | - | **`False` (Làm dở / Chưa nộp đủ)** |
| Yêu cầu Coding, hoàn thành $N/N$ bài con | Yêu cầu Game, chưa hoàn thành | COMPLETED | NOT_SUBMITTED | **`False` (Làm dở / Thiếu Game)** |
| Chưa làm bài nào | Chưa làm bài nào | NOT_SUBMITTED | NOT_SUBMITTED | **`False` (Chưa nộp)** |

---

## 3. Application DTOs

### `HomeworkResponse` (`backend/app/homework/application/dtos.py`)
Bổ sung các trường tiến độ chi tiết cho DTO danh sách bài tập:

```python
class HomeworkResponse(HomeworkBase):
    id: int
    deadline: datetime | None = None
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None

    # Computed fields
    submission_count: int = 0
    is_submitted: bool | None = None
    is_overdue: bool | None = None
    has_coding: bool = False
    coding_submitted: bool = False
    has_game: bool = False
    game_submitted: bool = False
    uncompleted_items: list[str] = Field(default_factory=list)
    
    # Bổ sung các trường tiến độ mới
    coding_status: str = "NOT_SUBMITTED"
    total_coding_required: int = 0
    total_coding_completed: int = 0
```

---

## 4. Frontend Types

### `Homework` (`frontend/src/features/homework/types/homework.types.ts`)
Bổ sung typing trên Frontend:

```typescript
export interface Homework {
    id: number;
    title: string;
    deadline?: string | null;
    link?: string | null;
    slug?: string | null;
    requires_coding: boolean;
    requires_game: boolean;
    created_at: string;
    updated_at: string;
    created_by?: number | null;
    submission_count?: number;
    is_submitted?: boolean | null;
    is_overdue?: boolean | null;
    has_coding?: boolean;
    coding_submitted?: boolean;
    has_game?: boolean;
    game_submitted?: boolean;
    uncompleted_items?: string[];
    // Bổ sung các trường tiến độ mới
    coding_status?: 'COMPLETED' | 'PARTIALLY_SUBMITTED' | 'NOT_SUBMITTED';
    total_coding_required?: number;
    total_coding_completed?: number;
    coding_exercises?: ExerciseSummary[];
}
```
