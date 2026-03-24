from typing import Optional

from app.shared.base_model import TimestampMixin
from app.user.domain.user_entity import User, UserStatus
from sqlmodel import Column
from sqlmodel import Enum as SQLEnum
from sqlmodel import Field


class UserModel(TimestampMixin, table=True):
    """SQLModel model for users."""

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    email: str = Field(max_length=255, unique=True, index=True)
    phone_number: Optional[str] = Field(default=None, max_length=20)

    status: UserStatus = Field(
        default=UserStatus.ACTIVE, sa_column=Column(SQLEnum(UserStatus))
    )

    discord_id: Optional[str] = Field(default=None, max_length=255)
    zalo_id: Optional[str] = Field(default=None, max_length=255)
    zalo_bot_id: Optional[str] = Field(default=None, max_length=255)
    zalo_bind_code: Optional[str] = Field(default=None, max_length=10)
    avatar_url: Optional[str] = Field(default=None)

    role_id: Optional[int] = Field(default=None, foreign_key="roles.id")
    account_id: Optional[int] = Field(default=None, foreign_key="accounts.id")

    def to_entity(self) -> User:
        return User(
            id=self.id,  # type: ignore
            email=self.email,
            name=self.name,
            phone_number=self.phone_number,
            avatar_url=self.avatar_url,
            discord_id=self.discord_id,
            zalo_id=self.zalo_id,
            zalo_bot_id=self.zalo_bot_id,
            zalo_bind_code=self.zalo_bind_code,
            status=self.status,
            role_id=self.role_id,
            account_id=self.account_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_deleted=self.is_deleted,
        )

    @classmethod
    def from_entity(cls, user: User) -> "UserModel":
        return cls(
            id=user.id,
            email=user.email,
            name=user.name,
            phone_number=user.phone_number,
            avatar_url=user.avatar_url,
            discord_id=user.discord_id,
            zalo_id=user.zalo_id,
            zalo_bot_id=user.zalo_bot_id,
            zalo_bind_code=user.zalo_bind_code,
            status=user.status,
            role_id=user.role_id,
            account_id=user.account_id,
            created_at=user.created_at,
            updated_at=user.updated_at,
            is_deleted=user.is_deleted,
        )
