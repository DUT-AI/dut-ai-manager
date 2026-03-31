"""
Shared Value Objects — reusable across all domain modules.

Value Objects are immutable, compared by value (not identity).
"""

from pydantic import BaseModel, ConfigDict


class UserRef(BaseModel):
    """Value Object — lightweight reference to a User.

    Used when a domain entity needs to know WHO (user info)
    without depending on the full User entity.

    Examples:
        violation.owner    → user who was violated
        violation.creator  → who created this violation
        meeting.creator    → who scheduled the meeting
    """

    model_config = ConfigDict(frozen=True)

    id: int
    name: str = ""
    avatar: str | None = None
    discord_id: str | None = None
