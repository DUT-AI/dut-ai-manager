# Data Model: Tối Ưu Và Dọn Dẹp Domain Homework

**Feature**: `003-homework-cleanup` | **Date**: 2026-09-25

---

## 1. Database Schema (PostgreSQL)

### Bảng `homeworks`
Lưu trữ thông tin cốt lõi của bài tập.

```sql
CREATE TABLE homeworks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    deadline TIMESTAMP WITH TIME ZONE NOT NULL,
    link VARCHAR(500) NULL,
    slug VARCHAR(255) NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by INTEGER NULL,
    updated_by INTEGER NULL,
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE INDEX ix_homeworks_title ON homeworks (title);
CREATE INDEX ix_homeworks_deadline ON homeworks (deadline);
CREATE INDEX ix_homeworks_is_deleted ON homeworks (is_deleted);
```

---

### Bảng `homework_assignees`
Lưu trữ danh sách thành viên cá nhân được phân công làm bài tập.

```sql
CREATE TABLE homework_assignees (
    id SERIAL PRIMARY KEY,
    homework_id INTEGER NOT NULL REFERENCES homeworks(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by INTEGER NULL,
    updated_by INTEGER NULL,
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE INDEX ix_homework_assignees_homework_id ON homework_assignees (homework_id);
CREATE INDEX ix_homework_assignees_user_id ON homework_assignees (user_id);
```

---

### Bảng bị XÓA BỎ: `homework_teams`
Thực hiện `DROP TABLE homework_teams CASCADE;` thông qua Alembic migration.

```sql
-- Migration drop
DROP TABLE IF EXISTS homework_teams CASCADE;
```

---

## 2. SQLAlchemy Models

### `HomeworkModel` (`app/homework/infrastructure/model.py`)

```python
class HomeworkModel(SQLAlchemyTimestampMixin, Base):
    __tablename__ = "homeworks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    deadline: Mapped[datetime] = mapped_column(index=True)
    link: Mapped[str | None] = mapped_column(String(500), default=None, nullable=True)
    slug: Mapped[str | None] = mapped_column(String(255), default=None, nullable=True)

    assignees: Mapped[list["HomeworkAssigneeModel"]] = relationship(
        back_populates="homework", cascade="all, delete-orphan", lazy="selectin"
    )

    def to_entity(self) -> HomeworkEntity:
        return HomeworkEntity(
            id=self.id,
            title=self.title,
            deadline=self.deadline,
            link=self.link,
            slug=self.slug,
            assignee_ids=[a.user_id for a in self.assignees] if self.assignees else [],
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_deleted=self.is_deleted,
        )
```

---

### `HomeworkAssigneeModel` (`app/homework/infrastructure/model.py`)

```python
class HomeworkAssigneeModel(SQLAlchemyTimestampMixin, Base):
    __tablename__ = "homework_assignees"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    homework_id: Mapped[int] = mapped_column(ForeignKey("homeworks.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    homework: Mapped[HomeworkModel] = relationship(back_populates="assignees")
```

---

## 3. Domain Entities

### `Homework` (`app/homework/domain/entity.py`)

```python
class Homework(BaseEntity):
    title: str
    deadline: datetime
    link: str | None = None
    slug: str | None = None
    assignee_ids: list[int] = []
```
*(Đã loại bỏ `team_ids` và `submissions`)*
