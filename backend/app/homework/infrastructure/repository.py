from typing import Any, cast

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.sql.functions import count

from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.infrastructure.model import (
    HomeworkAssigneeModel,
    HomeworkModel,
    HomeworkTeamModel,
)


class HomeworkRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(
        self, skip: int = 0, limit: int = 100, deleted: bool = False
    ) -> list[HomeworkEntity]:
        """Get all homeworks optionally with pagination."""
        statement = (
            select(HomeworkModel)
            .where(HomeworkModel.is_deleted == deleted)
            .order_by(
                desc(
                    cast(
                        Any,
                        (
                            HomeworkModel.updated_at
                            if deleted
                            else HomeworkModel.created_at
                        ),
                    )
                )
            )
            .offset(skip)
            .limit(limit)
        )
        models = self.session.scalars(statement).all()
        return [m.to_entity() for m in models]

    def get_by_id(self, homework_id: int) -> HomeworkEntity | None:
        statement = (
            select(HomeworkModel)
            .where(
                HomeworkModel.id == homework_id,
                HomeworkModel.is_deleted == False,  # noqa: E712
            )
        )
        model = self.session.scalars(statement).first()
        return model.to_entity() if model else None

    def create(self, homework: HomeworkEntity) -> HomeworkEntity:
        model = HomeworkModel.from_entity(homework)
        self.session.add(model)
        self.session.flush()

        if homework.assignee_ids:
            for uid in homework.assignee_ids:
                self.session.add(HomeworkAssigneeModel(homework_id=model.id, user_id=uid))
        if homework.team_ids:
            for tid in homework.team_ids:
                self.session.add(HomeworkTeamModel(homework_id=model.id, team_id=tid))
        self.session.flush()
        return model.to_entity()

    def update(self, homework: HomeworkEntity) -> HomeworkEntity | None:
        statement = select(HomeworkModel).where(HomeworkModel.id == homework.id)
        model = self.session.scalars(statement).first()
        if model:
            model.title = homework.title
            model.deadline = homework.deadline
            model.link = homework.link
            model.slug = homework.slug
            self.session.add(model)
            self.session.flush()

            self.sync_assignees_and_teams(homework.id, homework.assignee_ids, homework.team_ids)
            return model.to_entity()
        return None

    def sync_assignees_and_teams(
        self, homework_id: int, assignee_ids: list[int] | None, team_ids: list[int] | None
    ):
        if assignee_ids is not None:
            existing_assignees = self.session.scalars(
                select(HomeworkAssigneeModel).where(HomeworkAssigneeModel.homework_id == homework_id)
            ).all()
            for a in existing_assignees:
                self.session.delete(a)
            for uid in assignee_ids:
                self.session.add(HomeworkAssigneeModel(homework_id=homework_id, user_id=uid))

        if team_ids is not None:
            existing_teams = self.session.scalars(
                select(HomeworkTeamModel).where(HomeworkTeamModel.homework_id == homework_id)
            ).all()
            for t in existing_teams:
                self.session.delete(t)
            for tid in team_ids:
                self.session.add(HomeworkTeamModel(homework_id=homework_id, team_id=tid))

        self.session.flush()

    def get_assigned_user_ids(self, homework_id: int) -> set[int]:
        """Lấy danh sách user_id được phân làm homework (gồm cá nhân + thành viên thuộc team)."""
        direct_uids = set(
            self.session.scalars(
                select(HomeworkAssigneeModel.user_id).where(
                    HomeworkAssigneeModel.homework_id == homework_id,
                    HomeworkAssigneeModel.is_deleted == False,
                )
            ).all()
        )
        team_ids = self.session.scalars(
            select(HomeworkTeamModel.team_id).where(
                HomeworkTeamModel.homework_id == homework_id,
                HomeworkTeamModel.is_deleted == False,
            )
        ).all()

        team_uids = set()
        if team_ids:
            from app.team.infrastructure.model import TeamMemberModel
            team_uids = set(
                self.session.scalars(
                    select(TeamMemberModel.user_id).where(
                        TeamMemberModel.team_id.in_(team_ids),
                        TeamMemberModel.is_deleted == False,
                    )
                ).all()
            )

        return direct_uids | team_uids

    def get_by_deadline_date(self, target_date: Any) -> list[HomeworkEntity]:
        statement = (
            select(HomeworkModel)
            .options(
                selectinload(HomeworkModel.submissions).joinedload(
                    HomeworkSubmissionModel.owner
                )
            )
            .where(
                HomeworkModel.is_deleted == False,
                func.date(HomeworkModel.deadline) == target_date,
            )
        )
        models = self.session.scalars(statement).all()
        return [m.to_entity() for m in models]

    def delete_by_id(self, homework_id: int) -> bool:
        statement = select(HomeworkModel).where(HomeworkModel.id == homework_id)
        model = self.session.scalars(statement).first()
        if model:
            model.is_deleted = True
            self.session.add(model)
            self.session.flush()
            return True
        return False

    def restore(self, homework_id: int) -> HomeworkEntity | None:
        statement = select(HomeworkModel).where(
            HomeworkModel.id == homework_id,
            HomeworkModel.is_deleted == True,
        )
        model = self.session.scalars(statement).first()
        if model:
            model.is_deleted = False
            self.session.add(model)
            self.session.flush()
            return model.to_entity()
        return None
