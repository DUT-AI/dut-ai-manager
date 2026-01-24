from datetime import datetime
from typing import TYPE_CHECKING, Optional

from app.models.base import TimestampMixin
from sqlmodel import Field, Relationship

if TYPE_CHECKING:
    from app.models.user import User


class Violation(TimestampMixin, table=True):
    """Violation model"""

    __tablename__ = "violations"

    id: Optional[int] = Field(default=None, primary_key=True)
    reason: str = Field(max_length=500)
    date: datetime = Field(index=True)

    # Foreign keys
    user_id: int = Field(foreign_key="users.id", index=True)

    # Relationships
    user: "User" = Relationship(
        back_populates="violations",
        sa_relationship_kwargs={"foreign_keys": "[Violation.user_id]"},
    )
    creator: Optional["User"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "Violation.created_by==User.id",
            "foreign_keys": "[Violation.created_by]",
        }
    )
    updater: Optional["User"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "Violation.updated_by==User.id",
            "foreign_keys": "[Violation.updated_by]",
        }
    )

    @property
    def user_name(self) -> Optional[str]:
        return self.user.name if self.user else None

    @property
    def user_avatar(self) -> Optional[str]:
        return self.user.avatar_url if self.user else None

    @property
    def creator_name(self) -> Optional[str]:
        return self.creator.name if self.creator else None

    @property
    def updater_name(self) -> Optional[str]:
        return self.updater.name if self.updater else None
