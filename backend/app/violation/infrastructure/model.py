"""
Violation ORM Model — SQLModel, infrastructure layer.

Only used for database mapping and entity conversion.
Domain entity: app.violation.domain.entity.Violation
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from app.shared.domain.value_objects import UserRef
from app.shared.infrastructure.base_model import TimestampMixin
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
        from app.violation.domain.entity import Violation
        from typing import cast
        from sqlalchemy import inspect
        
        insp = inspect(self)
        owner_ref = None
        if insp is not None and "user" not in insp.unloaded and self.user:
            owner_ref = UserRef(
                id=cast(int, self.user.id),
                name=self.user.name,
                avatar=self.user.avatar_url,
                discord_id=self.user.discord_id,
                zalo_bot_id=self.user.zalo_bot_id,
            )

        creator_ref = None
        if insp is not None and "creator_rel" not in insp.unloaded and self.creator_rel:
            creator_ref = UserRef(
                id=cast(int, self.creator_rel.id),
                name=self.creator_rel.name,
                avatar=self.creator_rel.avatar_url,
                discord_id=self.creator_rel.discord_id,
                zalo_bot_id=self.creator_rel.zalo_bot_id,
            )

        updater_ref = None
        if insp is not None and "updater_rel" not in insp.unloaded and self.updater_rel:
            updater_ref = UserRef(
                id=cast(int, self.updater_rel.id),
                name=self.updater_rel.name,
                avatar=self.updater_rel.avatar_url,
                discord_id=self.updater_rel.discord_id,
                zalo_bot_id=self.updater_rel.zalo_bot_id,
            )

        return Violation(
            id=self.id,
            reason=self.reason,
            date=self.date,
            user_id=self.user_id,
            created_by=self.created_by,
            updated_by=self.updated_by,
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_deleted=self.is_deleted,
            owner=owner_ref,
            creator=creator_ref,
            updater=updater_ref,
        )

    @classmethod
    def from_entity(cls, entity: Any) -> "ViolationModel":
        """Domain Entity → ORM Model."""
        # Note: Use Any to avoid circular import issues with BaseEntity at class level
        # if needed, but typed correctly here for the implementation.
        return cls(
            id=entity.id,
            reason=entity.reason,
            date=entity.date or datetime.now(),
            user_id=entity.user_id,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
            created_at=entity.created_at or datetime.now(),
            updated_at=entity.updated_at or datetime.now(),
            is_deleted=entity.is_deleted,
        )
