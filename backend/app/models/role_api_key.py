from typing import TYPE_CHECKING, Optional

from app.models.base import TimestampMixin
from sqlmodel import Field, Relationship

if TYPE_CHECKING:
    from app.models.role import Role


class RoleApiKey(TimestampMixin, table=True):
    """API Key for Role-based access"""

    __tablename__ = "role_api_keys"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    key_hash: str = Field(index=True)  # Store hashed key only
    prefix: str = Field(max_length=10)  # Store prefix for ID purposes (e.g. sk-...)
    is_active: bool = Field(default=True)

    role_id: int = Field(foreign_key="roles.id", index=True)

    # Relationships
    role: "Role" = Relationship(back_populates="api_keys")
