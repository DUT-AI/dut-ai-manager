"""
Bonus Point ORM Model — SQLModel, infrastructure layer.

Only used for database mapping and entity conversion.
Domain entity: app.bonus_point.domain.entity.BonusPoint
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from app.bonus_point.domain.entity import BonusPoint
from app.shared.domain.value_objects import UserRef
from app.shared.infrastructure.base_model import TimestampMixin
from sqlmodel import Field, Relationship

if TYPE_CHECKING:
    from app.user.infrastructure.model import UserModel


class BonusPointModel(TimestampMixin, table=True):
    """ORM model — maps to 'bonus_points' table."""

    __tablename__ = "bonus_points"

    id: Optional[int] = Field(default=None, primary_key=True)
    points: int = Field()
    reason: str = Field(max_length=500)
    date: datetime = Field(index=True)

    # Foreign keys
    user_id: int = Field(foreign_key="users.id", index=True)

    # Relationships (ORM concern only)
    user: "UserModel" = Relationship(
        back_populates="bonus_points",
        sa_relationship_kwargs={"foreign_keys": "[BonusPointModel.user_id]"},
    )
    creator: Optional["UserModel"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "BonusPointModel.created_by==UserModel.id",
            "foreign_keys": "[BonusPointModel.created_by]",
            "overlaps": "bonus_points",
        }
    )
    updater: Optional["UserModel"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "BonusPointModel.updated_by==UserModel.id",
            "foreign_keys": "[BonusPointModel.updated_by]",
            "overlaps": "bonus_points",
        }
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
            updated_by=self.updated_by,  # type: ignore
            created_at=self.created_at,  # type: ignore
            updated_at=self.updated_at,  # type: ignore
            is_deleted=self.is_deleted,  # type: ignore
            owner=(
                UserRef(
                    id=self.user.id,  # type: ignore
                    name=self.user.name,  # type: ignore
                    avatar_url=self.user.avatar_url,  # type: ignore
                )
                if self.user
                else None
            ),
            creator=(
                UserRef(
                    id=self.creator.id,  # type: ignore
                    name=self.creator.name,  # type: ignore
                    avatar_url=self.creator.avatar_url,  # type: ignore
                )
                if self.creator
                else None
            ),
            updater=(
                UserRef(
                    id=self.updater.id,  # type: ignore
                    name=self.updater.name,  # type: ignore
                    avatar_url=self.updater.avatar_url,  # type: ignore
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
