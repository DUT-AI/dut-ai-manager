"""Tool to retrieve official club and lab violation policies."""

from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.chatbot.infrastructure.tools.base import BaseChatbotTool
from app.core.principal import AuthPrincipal


class GetViolationPoliciesTool(BaseChatbotTool):
    name = "get_violation_policies"
    description = (
        "Tra cứu tài liệu quy chế chính thức về điểm danh, đi trễ, vắng họp, "
        "nộp bài tập muộn và quy trình nộp đơn xin phép của CLB/Lab."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Chủ đề quy chế cần tra cứu (ví dụ: 'điểm danh', 'bài tập', 'xin phép', 'khiếu nại')",
            }
        },
        "required": [],
    }
    required_permissions = []  # Open to all authenticated members

    def __init__(self, policy_file_path: Path | None = None) -> None:
        self.policy_file = (
            policy_file_path
            or Path(__file__).parents[1] / "knowledge" / "violation_policies.md"
        )

    def execute(
        self, session: Session, args: dict[str, Any], user: AuthPrincipal
    ) -> dict[str, Any]:
        try:
            if self.policy_file.exists():
                content = self.policy_file.read_text(encoding="utf-8")
                return {"policy_document": content}
        except Exception:
            pass
        return {
            "policy_document": (
                "Quy chế CLB: Đi trễ trừ 1 điểm, vắng họp không phép trừ 2 điểm, "
                "nộp bài muộn trừ 1 điểm. Mọi thắc mắc liên hệ HR."
            )
        }
