from typing import List, Optional

from app.team.application.dtos import (TeamCreate, TeamMemberResponse,
                                       TeamResponse, TeamUpdate)
from app.team.domain.entity import Team as TeamEntity
from app.team.infrastructure.repository import TeamRepository
from loguru import logger


class TeamUseCases:
    def __init__(self, repository: TeamRepository):
        self.repository = repository

    def _map_to_response(self, team: TeamEntity) -> TeamResponse:
        members = []
        for tm in team.members:
            members.append(
                TeamMemberResponse(
                    user_id=tm.user_id,
                    user_name=tm.user_name,
                    email=tm.email,
                    user_avatar=tm.user_avatar,
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

    def get_all(self, skip: int = 0, limit: int = 100) -> List[TeamResponse]:
        teams = self.repository.get_all_with_members(skip, limit)
        return [self._map_to_response(t) for t in teams]

    def get_by_id(self, team_id: int) -> Optional[TeamResponse]:
        team = self.repository.get_by_id_with_members(team_id)
        return self._map_to_response(team) if team else None

    def create(self, data: TeamCreate) -> TeamResponse:
        team = TeamEntity(team_name=data.team_name)
        new_team = self.repository.create(team)

        if data.member_ids is not None:
            self.repository.sync_members(new_team.id, data.member_ids)

        # Reload to get relationships
        team_reloaded = self.repository.get_by_id_with_members(new_team.id)
        return self._map_to_response(team_reloaded)

    def update(self, team_id: int, data: TeamUpdate) -> Optional[TeamResponse]:
        team = self.repository.get_by_id(team_id)
        if not team:
            return None

        if data.team_name is not None:
            team.team_name = data.team_name
            self.repository.update(team)

        if data.member_ids is not None:
            self.repository.sync_members(team_id, data.member_ids)

        # Reload
        team_reloaded = self.repository.get_by_id_with_members(team_id)
        return self._map_to_response(team_reloaded)

    def delete(self, team_id: int) -> bool:
        return self.repository.delete(team_id)

    def is_in_same_team(self, user_id: int, target_user_id: int) -> bool:
        """Check if two users belong to at least one common team"""
        user_teams = set(self.repository.get_team_ids_by_user(user_id))
        target_teams = set(self.repository.get_team_ids_by_user(target_user_id))
        logger.debug(f"User teams = {user_teams}")
        logger.debug(f"Target teams = {target_teams}")
        return bool(user_teams & target_teams)
