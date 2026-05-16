"""
Bonus Point ORM Model — SQLAlchemy 2.0, infrastructure layer.

Only used for database mapping and entity conversion.
Domain entity: app.bonus_point.domain.entity.BonusPoint
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.bonus_point.domain.entity import BonusPoint
from app.shared.domain.value_objects import UserRef
from app.shared.infrastructure.base_model import Base, SQLAlchemyTimestampMixin

if TYPE_CHECKING:
    from app.user.infrastructure.model import UserModel


class BonusPointModel(SQLAlchemyTimestampMixin, Base):
    """ORM model — maps to 'bonus_points' table."""

    __tablename__ = "bonus_points"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    points: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(500))
    date: Mapped[datetime] = mapped_column(DateTime, index=True)

    # Foreign keys
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # Relationships (ORM concern only)
    user: Mapped["UserModel"] = relationship(
        back_populates="bonus_points",
        foreign_keys=[user_id],
    )
    creator: Mapped["UserModel | None"] = relationship(
        primaryjoin="BonusPointModel.created_by==UserModel.id",
        foreign_keys="BonusPointModel.created_by",
        overlaps="bonus_points",
    )
    updater: Mapped["UserModel | None"] = relationship(
        primaryjoin="BonusPointModel.updated_by==UserModel.id",
        foreign_keys="BonusPointModel.updated_by",
        overlaps="bonus_points",
    )

    # --- Mapping methods ---

    def to_entity(self) -> BonusPoint:
        """ORM Model → Domain Entity with UserRef Value Objects."""

        return BonusPoint(
            id=self.id,
            points=self.points,
            reason=self.reason,
            date=self.date,
            user_id=self.user_id,
            created_by=self.created_by,
            updated_by=self.updated_by,
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_deleted=self.is_deleted,
            owner=(
                UserRef(
                    id=self.user.id,
                    name=self.user.name,
                    avatar_url=self.user.avatar_url,
                )
                if self.user
                else None
            ),
            creator=(
                UserRef(
                    id=self.creator.id,
                    name=self.creator.name,
                    avatar_url=self.creator.avatar_url,
                )
                if self.creator
                else None
            ),
            updater=(
                UserRef(
                    id=self.updater.id,
                    name=self.updater.name,
                    avatar_url=self.updater.avatar_url,
                )
                if self.updater
                else None
            ),
        )

    @classmethod
    def from_entity(cls, entity: BonusPoint) -> "BonusPointModel":
        """Domain Entity → ORM Model."""
        return cls(
            id=entity.id,
            points=entity.points,
            reason=entity.reason,
            date=entity.date,
            user_id=entity.user_id,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            is_deleted=entity.is_deleted,
        )
