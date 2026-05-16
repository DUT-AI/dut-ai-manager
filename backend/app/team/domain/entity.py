from app.shared.domain.base_entity import BaseEntity


class TeamMemberInfo(BaseEntity):
    """Domain model representing a member's basic info inside a team context."""

    user_id: int
    user_name: str
    email: str
    user_avatar_url: str | None = None


class Team(BaseEntity):
    """Domain entity for a Team."""

    team_name: str
    members: list[TeamMemberInfo] = []
    member_ids: list[int] = []

    @property
    def member_count(self) -> int:
        return len(self.members)
