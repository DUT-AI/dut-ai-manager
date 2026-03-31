from typing import Optional

from app.auth.domain.auth_user_entity import AuthUser
from app.shared.base_model import TimestampMixin
from sqlmodel import Field, Relationship


class AccountModel(TimestampMixin, table=True):
    """SQLModel model for accounts."""

    __tablename__ = "accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    hash_password: str = Field(max_length=255)

    # Note: user relationship is left as in User's request.
    # Since UserModel specifies account_id foreign_key, the relationship connects here.

    def to_entity(self) -> AuthUser:
        from app.user.domain.value_objects import UserStatus

        return AuthUser(
            id=self.id,  # type: ignore
            email="",
            status=UserStatus.ACTIVE,
            hashed_password=self.hash_password,
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_deleted=self.is_deleted,
            created_by=self.created_by,
            updated_by=self.updated_by,
        )

    @classmethod
    def from_entity(cls, entity: AuthUser) -> "AccountModel":
        return cls(
            id=entity.id,  # type: ignore
            hash_password=entity.hashed_password,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            is_deleted=entity.is_deleted,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
        )
