"""
Violation ORM Model — SQLAlchemy 2.0, infrastructure layer.

Only used for database mapping and entity conversion.
Domain entity: app.violation.domain.entity.Violation
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.domain.value_objects import UserRef
from app.shared.infrastructure.base_model import Base, SQLAlchemyTimestampMixin

if TYPE_CHECKING:
    from app.user.infrastructure.model import UserModel
    from app.violation.domain.entity import Violation


class ViolationModel(SQLAlchemyTimestampMixin, Base):
    """ORM model — maps to 'violations' table."""

    __tablename__ = "violations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    reason: Mapped[str] = mapped_column(String(500))
    date: Mapped[datetime] = mapped_column(DateTime, index=True)

    # Foreign keys
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # Relationships (ORM concern only)
    user: Mapped["UserModel"] = relationship(
        back_populates="violations",
        foreign_keys=[user_id],
    )
    creator_rel: Mapped["UserModel | None"] = relationship(
        primaryjoin="ViolationModel.created_by==UserModel.id",
        foreign_keys="ViolationModel.created_by",
        overlaps="violations",
    )
    updater_rel: Mapped["UserModel | None"] = relationship(
        primaryjoin="ViolationModel.updated_by==UserModel.id",
        foreign_keys="ViolationModel.updated_by",
        overlaps="violations,creator_rel",
    )

    # --- Mapping methods ---

    def to_entity(self) -> "Violation":
        """ORM Model → Domain Entity with UserRef Value Objects."""
        from sqlalchemy import inspect

        from app.violation.domain.entity import Violation

        insp = inspect(self)
        owner_ref = None
        if insp is not None and "user" not in insp.unloaded and self.user:
            owner_ref = UserRef(
                id=self.user.id,
                name=self.user.name,
                avatar_url=self.user.avatar_url,
            )

        creator_ref = None
        if insp is not None and "creator_rel" not in insp.unloaded and self.creator_rel:
            creator_ref = UserRef(
                id=self.creator_rel.id,
                name=self.creator_rel.name,
                avatar_url=self.creator_rel.avatar_url,
            )

        updater_ref = None
        if insp is not None and "updater_rel" not in insp.unloaded and self.updater_rel:
            updater_ref = UserRef(
                id=self.updater_rel.id,
                name=self.updater_rel.name,
                avatar_url=self.updater_rel.avatar_url,
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
        return cls(
            id=entity.id,
            reason=entity.reason,
            date=entity.date or datetime.now(),
            user_id=entity.user_id,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
            is_deleted=entity.is_deleted,
        )
