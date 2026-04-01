from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from app.shared.domain.base_entity import BaseEntity


@dataclass
class TeamMemberInfo:
    """Domain model representing a member's basic info inside a team context."""

    user_id: int
    user_name: str
    email: str
    user_avatar: Optional[str] = None


@dataclass
class Team(BaseEntity):
    """Domain entity for a Team."""

    team_name: str
    members: List[TeamMemberInfo] = field(default_factory=list)
    member_ids: List[int] = field(default_factory=list)

    @property
    def member_count(self) -> int:
        return len(self.members)
