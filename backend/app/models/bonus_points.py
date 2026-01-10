from datetime import datetime
from typing import TYPE_CHECKING, Optional

from app.models.base import TimestampMixin
from sqlmodel import Field, Relationship

if TYPE_CHECKING:
    from app.models.user import User


class BonusPoint(TimestampMixin, table=True):
    """Bonus Point model"""

    __tablename__ = "bonus_points"

    id: Optional[int] = Field(default=None, primary_key=True)
    points: int = Field()
    reason: str = Field(max_length=500)
    date: datetime = Field(index=True)

    # Foreign keys
    user_id: int = Field(foreign_key="users.id", index=True)

    # Relationships
    user: "User" = Relationship(
        back_populates="bonus_points",
        sa_relationship_kwargs={"foreign_keys": "[BonusPoint.user_id]"},
    )
    creator: Optional["User"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "BonusPoint.created_by==User.id",
            "foreign_keys": "[BonusPoint.created_by]",
        }
    )
    updater: Optional["User"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "BonusPoint.updated_by==User.id",
            "foreign_keys": "[BonusPoint.updated_by]",
        }
    )

    @property
    def user_name(self) -> Optional[str]:
        return self.user.name if self.user else None

    @property
    def creator_name(self) -> Optional[str]:
        return self.creator.name if self.creator else None

    @property
    def updater_name(self) -> Optional[str]:
        return self.updater.name if self.updater else None
