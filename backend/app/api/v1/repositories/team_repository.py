from typing import List, Optional
from sqlalchemy.orm import joinedload
from sqlmodel import Session, select, delete
from app.api.v1.repositories.base import BaseRepository
from app.models.team import Team, TeamMember


class TeamRepository(BaseRepository[Team]):
    def __init__(self, session: Session):
        super().__init__(session, Team)

    def get_all_with_members(self, skip: int = 0, limit: int = 100) -> List[Team]:
        statement = (
            select(Team)
            .where(Team.is_deleted == False)
            .options(joinedload(Team.team_members).joinedload(TeamMember.user))
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.exec(statement).unique().all())

    def get_by_id_with_members(self, team_id: int) -> Optional[Team]:
        statement = (
            select(Team)
            .where(
                Team.is_deleted == False,
                Team.id == team_id,
            )
            .options(joinedload(Team.team_members).joinedload(TeamMember.user))
        )
        return self.session.exec(statement).first()

    def sync_members(self, team_id: int, user_ids: List[int]):
        # Get all existing members (including deleted ones)
        statement = select(TeamMember).where(TeamMember.team_id == team_id)
        existing_members = self.session.exec(statement).all()
        existing_map = {m.user_id: m for m in existing_members}

        # Process target user_ids
        for uid in user_ids:
            if uid in existing_map:
                # If exists, ensure it is active
                existing_map[uid].is_deleted = False
                self.session.add(existing_map[uid])
            else:
                # If new, create it
                member = TeamMember(team_id=team_id, user_id=uid)
                self.session.add(member)

        # Soft delete members not in target list
        for uid, member in existing_map.items():
            if uid not in user_ids:
                member.is_deleted = True
                self.session.add(member)

        self.session.commit()

    def get_team_ids_by_user(self, user_id: int) -> List[int]:
        """Get all team IDs that a user belongs to"""
        statement = select(TeamMember.team_id).where(
            TeamMember.is_deleted == False,
            TeamMember.user_id == user_id,
        )
        return list(self.session.exec(statement).all())

    def get_user_ids_by_teams(self, team_ids: List[int]) -> List[int]:
        """Get all user IDs from given teams"""
        statement = select(TeamMember.user_id).where(
            TeamMember.is_deleted == False,
            TeamMember.team_id.in_(team_ids),
        )
        return list(set(self.session.exec(statement).all()))
