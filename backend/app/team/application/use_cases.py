from app.team.application.dtos import (
    TeamCreate,
    TeamMemberResponse,
    TeamResponse,
    TeamUpdate,
)
from app.team.domain.entity import Team as TeamEntity
from app.team.infrastructure.repository import TeamRepository


class TeamUseCases:
    def __init__(self, repository: TeamRepository):
        self.repository = repository

    def _map_to_response(self, team: TeamEntity) -> TeamResponse:
        assert team.id is not None
        members = []
        for tm in team.members:
            members.append(
                TeamMemberResponse(
                    user_id=tm.user_id,
                    user_name=tm.user_name,
                    email=tm.email,
                    user_avatar_url=tm.user_avatar_url,
                )
            )

        return TeamResponse(
            id=team.id,
            team_name=team.team_name,
            created_at=team.created_at,
            updated_at=team.updated_at,
            member_count=team.member_count,
            members=members,
        )

    def get_all(self, skip: int = 0, limit: int = 100) -> list[TeamResponse]:
        teams = self.repository.get_all_with_members(skip, limit)
        return [self._map_to_response(t) for t in teams]

    def get_by_id(self, team_id: int) -> TeamResponse | None:
        team = self.repository.get_by_id_with_members(team_id)
        return self._map_to_response(team) if team else None

    def create(self, data: TeamCreate) -> TeamResponse:
        team = TeamEntity(team_name=data.team_name)
        new_team = self.repository.create(team)
        assert new_team.id is not None

        if data.member_ids is not None:
            self.repository.sync_members(new_team.id, data.member_ids)

        # Reload to get relationships
        team_reloaded = self.repository.get_by_id_with_members(new_team.id)
        if not team_reloaded:
            raise ValueError("Failed to reload team after creation")
        return self._map_to_response(team_reloaded)

    def update(self, team_id: int, data: TeamUpdate) -> TeamResponse | None:
        team = self.repository.get_by_id(team_id)
        if not team:
            return None

        if data.team_name is not None:
            team.team_name = data.team_name

        self.repository.update(team)

        if data.member_ids is not None:
            self.repository.sync_members(team_id, data.member_ids)

        # Reload to get relationships
        team_reloaded = self.repository.get_by_id_with_members(team_id)
        if not team_reloaded:
            return None
        return self._map_to_response(team_reloaded)

    def delete(self, team_id: int) -> bool:
        return self.repository.delete(team_id)
