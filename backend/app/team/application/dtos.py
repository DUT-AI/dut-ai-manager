from datetime import datetime

from pydantic import BaseModel


class TeamBase(BaseModel):
    team_name: str


class TeamCreate(TeamBase):
    member_ids: list[int] | None = []


class TeamUpdate(BaseModel):
    team_name: str | None = None
    member_ids: list[int] | None = None


class TeamMemberResponse(BaseModel):
    user_id: int
    user_name: str
    email: str
    user_avatar_url: str | None = None

    class Config:
        from_attributes = True


class TeamResponse(TeamBase):
    id: int
    created_at: datetime | None
    updated_at: datetime | None
    member_count: int = 0
    members: list[TeamMemberResponse] = []

    class Config:
        from_attributes = True
