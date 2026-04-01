"""
Violation ORM Model — SQLModel, infrastructure layer.

Only used for database mapping and entity conversion.
Domain entity: app.violation.domain.entity.Violation
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from app.shared.domain.value_objects import UserRef
from app.shared.infrastructure.base_model import TimestampMixin
from app.violation.domain.entity import Violation
from sqlmodel import Field, Relationship

if TYPE_CHECKING:
    from app.user.infrastructure.model import UserModel
    from app.violation.domain.entity import Violation


class ViolationModel(TimestampMixin, table=True):
    """ORM model — maps to 'violations' table."""

    __tablename__ = "violations"

    id: Optional[int] = Field(default=None, primary_key=True)
    reason: str = Field(max_length=500)
    date: datetime = Field(index=True)

    # Foreign keys
    user_id: int = Field(foreign_key="users.id", index=True)

    # Relationships (ORM concern only)
    user: "UserModel" = Relationship(
        back_populates="violations",
        sa_relationship_kwargs={"foreign_keys": "[ViolationModel.user_id]"},
    )
    creator_rel: Optional["UserModel"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "ViolationModel.created_by==UserModel.id",
            "foreign_keys": "[ViolationModel.created_by]",
            "overlaps": "violations",
        }
    )
    updater_rel: Optional["UserModel"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "ViolationModel.updated_by==UserModel.id",
            "foreign_keys": "[ViolationModel.updated_by]",
            "overlaps": "violations,creator_rel",
        }
    )

    # --- Mapping methods ---

    def to_entity(self) -> "Violation":
        """ORM Model → Domain Entity with UserRef Value Objects."""

        return Violation(
            id=self.id,
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
                    avatar=self.user.avatar_url,  # type: ignore
                    discord_id=self.user.discord_id,  # type: ignore
                )
                if self.user
                else None
            ),
            creator=(
                UserRef(
                    id=self.creator_rel.id,  # type: ignore
                    name=self.creator_rel.name,  # type: ignore
                    avatar=self.creator_rel.avatar_url,  # type: ignore
                    discord_id=self.creator_rel.discord_id,  # type: ignore
                )
                if self.creator_rel
                else None
            ),
            updater=(
                UserRef(
                    id=self.updater_rel.id,  # type: ignore
                    name=self.updater_rel.name,  # type: ignore
                    avatar=self.updater_rel.avatar_url,  # type: ignore
                    discord_id=self.updater_rel.discord_id,  # type: ignore
                )
                if self.updater_rel
                else None
            ),
        )
