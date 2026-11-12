"""Admin tool to summarize violation statistics across the club."""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.chatbot.infrastructure.tools.base import BaseChatbotTool
from app.core.permissions import ViolationPermission
from app.core.principal import AuthPrincipal
from app.user.infrastructure.model import UserModel
from app.violation.infrastructure.model import ViolationModel


class AdminSummarizeViolationsTool(BaseChatbotTool):
    name = "admin_summarize_violations"
    description = (
        "DÀNH CHO QUẢN TRỊ VIÊN/HR: Tổng hợp vi phạm toàn CLB trong tuần hoặc tháng gần nhất, "
        "liệt kê các thành viên có từ 3 vi phạm trở lên kèm họ tên và email."
    )
    parameters = {
        "type": "object",
        "properties": {
            "days": {
                "type": "integer",
                "description": "Khoảng thời gian cần thống kê theo số ngày gần nhất (ví dụ: 7 cho 1 tuần, 30 cho 1 tháng)",
                "default": 7,
            }
        },
        "required": [],
    }
    required_permissions = [ViolationPermission.READ.value]

    def execute(
        self, session: Session, args: dict[str, Any], user: AuthPrincipal
    ) -> dict[str, Any]:
        days = int(args.get("days", 7))
        cutoff = datetime.now(UTC) - timedelta(days=days)
        stmt = (
            select(ViolationModel)
            .where(
                ViolationModel.date >= cutoff,
                ViolationModel.is_deleted.is_(False),
            )
            .order_by(ViolationModel.date.desc())
        )
        violations = list(session.scalars(stmt).all())

        user_counts: dict[int, int] = {}
        for v in violations:
            user_counts[v.user_id] = user_counts.get(v.user_id, 0) + 1

        high_risk_user_ids = [uid for uid, count in user_counts.items() if count >= 3]
        users_map = {}
        if high_risk_user_ids:
            user_stmt = select(UserModel).where(UserModel.id.in_(high_risk_user_ids))
            users_map = {u.id: u for u in session.scalars(user_stmt).all()}

        high_risk_users = [
            {
                "user_id": uid,
                "name": users_map[uid].name if uid in users_map else f"Thành viên #{uid}",
                "email": users_map[uid].email if uid in users_map else None,
                "violation_count": count,
            }
            for uid, count in user_counts.items()
            if count >= 3
        ]

        return {
            "time_range_days": days,
            "total_violations_in_period": len(violations),
            "distinct_violators_count": len(user_counts),
            "members_with_3_or_more_violations": high_risk_users,
        }
