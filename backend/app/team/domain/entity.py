from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from app.shared.domain.base_entity import BaseEntity


class TeamMemberInfo(BaseEntity):
    """Domain model representing a member's basic info inside a team context."""

    user_id: int
    user_name: str
    email: str
    user_avatar_url: Optional[str] = None


class Team(BaseEntity):
    """Domain entity for a Team."""

    team_name: str
    members: List[TeamMemberInfo] = []
    member_ids: List[int] = []

    @property
    def member_count(self) -> int:
        return len(self.members)
