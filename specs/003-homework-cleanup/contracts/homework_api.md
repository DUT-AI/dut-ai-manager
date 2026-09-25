# API Contracts: Domain Homework

**Feature**: `003-homework-cleanup` | **Date**: 2026-09-25

---

## 1. DTO Schemas (`app/homework/application/dtos.py`)

### `HomeworkCreate`
```python
class HomeworkCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    deadline: datetime
    link: str | None = None
    slug: str | None = None
    assignee_ids: list[int] = Field(default_factory=list)
```

### `HomeworkUpdate`
```python
class HomeworkUpdate(BaseModel):
    title: str | None = None
    deadline: datetime | None = None
    link: str | None = None
    slug: str | None = None
    assignee_ids: list[int] | None = None
```

### `HomeworkResponse`
```python
class HomeworkResponse(BaseModel):
    id: int
    title: str
    deadline: datetime
    link: str | None = None
    slug: str | None = None
    assignee_ids: list[int] = []
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None
    updated_by: int | None = None
    is_deleted: bool = False
```

### `HomeworkSubmissionStatusResponse`
```python
class UserSubmissionInfo(BaseModel):
    user_id: int
    name: str | None = None
    avatar_url: str | None = None
    is_late: bool = False
    submitted_at: str | None = None

class CategorySubmissionStatus(BaseModel):
    submitted: list[UserSubmissionInfo] = []
    not_submitted: list[UserSubmissionInfo] = []

class HomeworkSubmissionStatusResponse(BaseModel):
    coding: CategorySubmissionStatus = Field(default_factory=CategorySubmissionStatus)
    game: CategorySubmissionStatus = Field(default_factory=CategorySubmissionStatus)
    submitted: list[UserSubmissionInfo] = []
    not_submitted: list[UserSubmissionInfo] = []
```

---

## 2. Endpoints Overview

| Method | Path | Mô tả | Request Body | Response |
|--------|------|-------|--------------|----------|
| `POST` | `/homeworks/` | Tạo bài tập mới | `HomeworkCreate` | `ApiResponse[HomeworkResponse]` |
| `GET` | `/homeworks/` | Lấy danh sách bài tập | Query params (paging, sort) | `ApiResponse[list[HomeworkResponse]]` |
| `GET` | `/homeworks/{id}` | Lấy chi tiết bài tập | N/A | `ApiResponse[HomeworkResponse]` |
| `PUT` | `/homeworks/{id}` | Cập nhật bài tập | `HomeworkUpdate` | `ApiResponse[HomeworkResponse]` |
| `DELETE`| `/homeworks/{id}` | Xóa mềm bài tập | N/A | `ApiResponse[bool]` |
| `GET` | `/homeworks/{id}/submission-status` | Xem tiến độ nộp bài (Quiz API) | N/A | `ApiResponse[HomeworkSubmissionStatusResponse]` |
| `POST` | `/homeworks/check-overdue` | Quét kiểm tra bài tập quá hạn hôm nay | N/A | `ApiResponse[dict]` |
| `POST` | `/homeworks/rescan-all` | Quét lại toàn bộ bài tập quá hạn trong quá khứ | N/A | `ApiResponse[dict]` |
