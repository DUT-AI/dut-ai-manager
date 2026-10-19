# Data Model: Tách Biệt `Homework` và `HomeworkAssignee`

## Domain Entities

### 1. `Homework` (Aggregate Root)
Đại diện cho đề bài tập trong hệ thống. Đã loại bỏ hoàn toàn `assignee_ids`.

```python
class Homework(BaseEntity):
    """Domain model containing assignment details."""

    title: str
    deadline: datetime
    link: str | None = None
    slug: str | None = None
    requires_coding: bool = True
    requires_game: bool = False
```

### 2. `HomeworkAssignee` (Relationship Model)
Được quản lý thông qua `HomeworkAssigneeRepository`.

```python
class HomeworkAssigneeModel(Base):
    __tablename__ = "homework_assignees"

    homework_id: int
    user_id: int
    is_deleted: bool
```

## Application DTOs (Preserved Contract)

Request DTOs từ client vẫn tiếp tục nhận `assignee_ids` để duy trì backward compatibility cho frontend:

```python
class CreateHomeworkRequest(BaseModel):
    title: str
    deadline: datetime
    link: str | None = None
    slug: str | None = None
    requires_coding: bool = True
    requires_game: bool = False
    assignee_ids: list[int] = Field(default_factory=list)
```
