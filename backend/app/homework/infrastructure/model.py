from datetime import datetime

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.homework.domain.entity import Homework as HomeworkEntity
from app.shared.infrastructure.base_model import Base, SQLAlchemyTimestampMixin


class HomeworkModel(SQLAlchemyTimestampMixin, Base):
    """Homework model containing assignment details"""

    __tablename__ = "homeworks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    deadline: Mapped[datetime] = mapped_column(index=True)
    link: Mapped[str | None] = mapped_column(String(500), default=None, nullable=True)
    slug: Mapped[str | None] = mapped_column(String(255), default=None, nullable=True)

    def to_entity(self) -> HomeworkEntity:
        return HomeworkEntity(
            id=self.id,
            title=self.title,
            deadline=self.deadline,
            link=self.link,
            slug=self.slug,
            submissions=[],
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_deleted=self.is_deleted,
        )

    @classmethod
    def from_entity(cls, entity: HomeworkEntity) -> "HomeworkModel":
        return cls(
            id=entity.id,
            title=entity.title,
            deadline=entity.deadline,
            link=entity.link,
            slug=entity.slug,
        )
