"""
Account ORM Model — SQLModel, infrastructure layer.
"""

from typing import TYPE_CHECKING, Optional

from app.auth.domain.entity import Account as AccountEntity
from app.shared.infrastructure.base_model import TimestampMixin

if TYPE_CHECKING:
    from app.user.infrastructure.model import UserModel
from sqlmodel import Field, Relationship


class AccountModel(TimestampMixin, table=True):
    """ORM model — maps to 'accounts' table."""

    __tablename__ = "accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    hash_password: str = Field(max_length=255)

    # Relationships
    user: Optional["UserModel"] = Relationship(
        back_populates="account",
        sa_relationship_kwargs={"foreign_keys": "[UserModel.account_id]"},
    )

    def to_entity(self) -> AccountEntity:
        """ORM Model → Domain Entity."""
        return AccountEntity(
            id=self.id,
            hash_password=self.hash_password,
            created_at=self.created_at,  # type: ignore
            updated_at=self.updated_at,  # type: ignore
            created_by=self.created_by,
            updated_by=self.updated_by,  # type: ignore
            is_deleted=self.is_deleted,  # type: ignore
        )

    @classmethod
    def from_entity(cls, entity: AccountEntity) -> "AccountModel":
        """Domain Entity → ORM Model."""
        return cls(
            id=entity.id,
            hash_password=entity.hash_password,
        )
