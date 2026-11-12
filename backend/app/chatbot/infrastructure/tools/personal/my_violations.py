"""Tool to fetch personal violations for the calling user."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.chatbot.infrastructure.tools.base import BaseChatbotTool
from app.core.principal import AuthPrincipal
from app.violation.infrastructure.model import ViolationModel


class GetMyViolationsTool(BaseChatbotTool):
    name = "get_my_violations"
    description = (
        "Tra cứu danh sách lịch sử các vi phạm cá nhân của chính người dùng hiện tại "
        "(lý do phạt, ngày vi phạm, loại vi phạm)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Số lượng bản ghi tối đa (mặc định 10)",
                "default": 10,
            }
        },
        "required": [],
    }
    required_permissions = []  # Open to all authenticated members

    def execute(
        self, session: Session, args: dict[str, Any], user: AuthPrincipal
    ) -> dict[str, Any]:
        limit = int(args.get("limit", 10))
        # Enforce strict IDOR protection: only query user.id
        stmt = (
            select(ViolationModel)
            .where(
                ViolationModel.user_id == user.id,
                ViolationModel.is_deleted.is_(False),
            )
            .order_by(ViolationModel.date.desc())
            .limit(limit)
        )
        models = session.scalars(stmt).all()
        records = [
            {
                "id": m.id,
                "date": m.date.strftime("%d/%m/%Y %H:%M") if m.date else "N/A",
                "reason": m.reason,
            }
            for m in models
        ]
        return {
            "total_violations": len(records),
            "user_id": user.id,
            "violations": records,
        }
