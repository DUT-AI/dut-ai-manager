from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

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

    assignees: Mapped[list["HomeworkAssigneeModel"]] = relationship(
        back_populates="homework", cascade="all, delete-orphan", lazy="selectin"
    )
    teams: Mapped[list["HomeworkTeamModel"]] = relationship(
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
            team_ids=[t.team_id for t in self.teams] if self.teams else [],
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


class HomeworkAssigneeModel(SQLAlchemyTimestampMixin, Base):
    """Mapping between Homework and direct User assignees"""

    __tablename__ = "homework_assignees"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    homework_id: Mapped[int] = mapped_column(ForeignKey("homeworks.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    homework: Mapped[HomeworkModel] = relationship(back_populates="assignees")


class HomeworkTeamModel(SQLAlchemyTimestampMixin, Base):
    """Mapping between Homework and Team assignees"""

    __tablename__ = "homework_teams"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    homework_id: Mapped[int] = mapped_column(ForeignKey("homeworks.id", ondelete="CASCADE"), index=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), index=True)

    homework: Mapped[HomeworkModel] = relationship(back_populates="teams")

