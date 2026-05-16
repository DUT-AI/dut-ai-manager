from sqlalchemy import select
from sqlalchemy.orm import Session, contains_eager

from app.team.domain.entity import Team as TeamEntity
from app.team.infrastructure.model import TeamMemberModel, TeamModel


class TeamRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all_with_members(self, skip: int = 0, limit: int = 100) -> list[TeamEntity]:
        statement = (
            select(TeamModel)
            .outerjoin(
                TeamMemberModel,
                (TeamModel.id == TeamMemberModel.team_id)
                & (TeamMemberModel.is_deleted == False),
            )
            .where(TeamModel.is_deleted == False)
            .options(
                contains_eager(TeamModel.team_members).joinedload(TeamMemberModel.user)
            )
            .offset(skip)
            .limit(limit)
        )
        models = self.session.scalars(statement).unique().all()
        return [model.to_entity() for model in models]

    def get_by_id_with_members(self, team_id: int) -> TeamEntity | None:
        statement = (
            select(TeamModel)
            .outerjoin(
                TeamMemberModel,
                (TeamModel.id == TeamMemberModel.team_id)
                & (TeamMemberModel.is_deleted == False),
            )
            .where(
                TeamModel.is_deleted == False,
                TeamModel.id == team_id,
            )
            .options(
                contains_eager(TeamModel.team_members).joinedload(TeamMemberModel.user)
            )
        )
        model = self.session.scalars(statement).unique().first()
        return model.to_entity() if model else None

    def get_by_id(self, team_id: int) -> TeamEntity | None:
        statement = select(TeamModel).where(
            TeamModel.id == team_id, TeamModel.is_deleted == False
        )
        model = self.session.scalars(statement).first()
        return model.to_entity() if model else None

    def create(self, team: TeamEntity) -> TeamEntity:
        model = TeamModel.from_entity(team)
        self.session.add(model)
        self.session.flush()
        return model.to_entity()

    def update(self, team: TeamEntity) -> None:
        statement = select(TeamModel).where(TeamModel.id == team.id)
        model = self.session.scalars(statement).first()
        if model:
            model.team_name = team.team_name
            self.session.add(model)

    def delete(self, team_id: int) -> bool:
        statement = select(TeamModel).where(TeamModel.id == team_id)
        model = self.session.scalars(statement).first()
        if model:
            model.is_deleted = True

            # also soft delete all team members mapping
            member_statement = select(TeamMemberModel).where(
                TeamMemberModel.team_id == team_id
            )
            members = self.session.scalars(member_statement).all()
            for m in members:
                m.is_deleted = True
                self.session.add(m)

            self.session.add(model)
            return True
        return False

    def sync_members(self, team_id: int, user_ids: list[int]):
        statement = select(TeamMemberModel).where(TeamMemberModel.team_id == team_id)
        existing_members = self.session.scalars(statement).all()
        existing_map = {m.user_id: m for m in existing_members}

        for uid in user_ids:
            if uid in existing_map:
                existing_map[uid].is_deleted = False
                self.session.add(existing_map[uid])
            else:
                member = TeamMemberModel(team_id=team_id, user_id=uid)
                self.session.add(member)

        for uid, member in existing_map.items():
            if uid not in user_ids:
                member.is_deleted = True
                self.session.add(member)

    def get_team_ids_by_user(self, user_id: int) -> list[int]:
        statement = select(TeamMemberModel.team_id).where(
            TeamMemberModel.is_deleted == False,
            TeamMemberModel.user_id == user_id,
        )
        return list(self.session.scalars(statement).all())

    def get_user_ids_by_teams(self, team_ids: list[int]) -> list[int]:
        statement = select(TeamMemberModel.user_id).where(
            TeamMemberModel.is_deleted == False,
            TeamMemberModel.team_id.in_(team_ids),
        )
        return list(set(self.session.scalars(statement).all()))
