"""
Account ORM Model — SQLAlchemy 2.0, infrastructure layer.
"""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.auth.domain.entity import Account as AccountEntity
from app.shared.infrastructure.base_model import Base, SQLAlchemyTimestampMixin

if TYPE_CHECKING:
    from app.user.infrastructure.model import UserModel


class AccountModel(SQLAlchemyTimestampMixin, Base):
    """ORM model — maps to 'accounts' table."""

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    hash_password: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), unique=True, index=True, default=None
    )

    # Relationships
    user: Mapped["UserModel | None"] = relationship(
        back_populates="account",
        foreign_keys=[user_id],
    )

    def to_entity(self) -> AccountEntity:
        """ORM Model → Domain Entity."""
        return AccountEntity(
            id=self.id,
            hash_password=self.hash_password,
            user_id=self.user_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_deleted=self.is_deleted,
        )

    @classmethod
    def from_entity(cls, entity: AccountEntity) -> "AccountModel":
        """Domain Entity → ORM Model."""
        return cls(
            id=entity.id,
            hash_password=entity.hash_password,
            user_id=entity.user_id,
        )
