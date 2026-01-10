from typing import TYPE_CHECKING, Optional

from app.models.base import TimestampMixin
from sqlmodel import Field, Relationship

if TYPE_CHECKING:
    from app.models.user import User


class Account(TimestampMixin, table=True):
    """Account model for authentication"""

    __tablename__ = "accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    hash_password: str = Field(max_length=255)

    # Relationships - use string for forward reference
    user: Optional["User"] = Relationship(
        back_populates="account",
        sa_relationship_kwargs={"foreign_keys": "User.account_id"},
    )
