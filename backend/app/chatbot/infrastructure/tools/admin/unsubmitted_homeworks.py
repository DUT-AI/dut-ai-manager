"""Admin tool to list unsubmitted homework assignees."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.chatbot.infrastructure.tools.base import BaseChatbotTool
from app.core.permissions import HomeworkPermission
from app.core.principal import AuthPrincipal
from app.homework.infrastructure.model import (
    HomeworkAssigneeModel,
    HomeworkModel,
    HomeworkSubmissionModel,
)
from app.user.infrastructure.model import UserModel


class AdminGetUnsubmittedHomeworksTool(BaseChatbotTool):
    name = "admin_get_unsubmitted_homeworks"
    description = (
        "DÀNH CHO MENTOR/TRAINER: Liệt kê danh sách chi tiết (họ tên, email) của các thành viên chưa nộp bài tập "
        "cho bài tập gần nhất hoặc theo tên bài tập."
    )
    parameters = {
        "type": "object",
        "properties": {
            "homework_title": {
                "type": "string",
                "description": "Tên bài tập cần tra cứu (để trống sẽ tra cứu bài tập mới nhất)",
            }
        },
        "required": [],
    }
    required_permissions = [HomeworkPermission.READ.value]

    def execute(
        self, session: Session, args: dict[str, Any], user: AuthPrincipal
    ) -> dict[str, Any]:
        stmt = (
            select(HomeworkModel)
            .order_by(HomeworkModel.id.desc())
        )
        homework_title = args.get("homework_title")
        if homework_title:
            stmt = stmt.where(HomeworkModel.title.ilike(f"%{homework_title}%"))

        hw = session.scalars(stmt).first()
        if not hw:
            return {"message": "Không tìm thấy bài tập phù hợp."}

        # Submissions for this homework
        sub_stmt = select(HomeworkSubmissionModel.user_id).where(
            HomeworkSubmissionModel.homework_id == hw.id
        )
        submitted_user_ids = set(session.scalars(sub_stmt).all())

        # All assignees for this homework joined with UserModel
        assignee_stmt = (
            select(HomeworkAssigneeModel, UserModel)
            .join(UserModel, UserModel.id == HomeworkAssigneeModel.user_id)
            .where(HomeworkAssigneeModel.homework_id == hw.id)
            .order_by(UserModel.name.asc())
        )
        assignee_results = session.execute(assignee_stmt).all()

        unsubmitted = [
            {
                "user_id": u.id,
                "name": u.name,
                "email": u.email,
                "deadline": (
                    assignee.deadline.strftime("%d/%m/%Y %H:%M")
                    if assignee.deadline
                    else None
                ),
            }
            for assignee, u in assignee_results
            if u.id not in submitted_user_ids
        ]

        # Representative deadline for this homework (latest or earliest assignee deadline if available)
        common_deadline = None
        if assignee_results and assignee_results[0][0].deadline:
            common_deadline = assignee_results[0][0].deadline.strftime("%d/%m/%Y %H:%M")

        return {
            "homework_id": hw.id,
            "homework_title": hw.title,
            "deadline": common_deadline,
            "unsubmitted_count": len(unsubmitted),
            "unsubmitted_members": unsubmitted,
        }

