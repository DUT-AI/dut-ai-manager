from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class TeamBase(BaseModel):
    team_name: str


class TeamCreate(TeamBase):
    member_ids: Optional[List[int]] = []


class TeamUpdate(BaseModel):
    team_name: Optional[str] = None
    member_ids: Optional[List[int]] = None


class TeamMemberResponse(BaseModel):
    user_id: int
    user_name: str
    email: str
    user_avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class TeamResponse(TeamBase):
    id: int
    created_at: datetime | None
    updated_at: datetime | None
    member_count: int = 0
    members: List[TeamMemberResponse] = []

    class Config:
        from_attributes = True
