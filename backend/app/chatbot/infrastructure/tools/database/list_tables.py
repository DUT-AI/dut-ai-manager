"""Tool to list all business database tables with overview descriptions."""

from typing import Any

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.chatbot.infrastructure.tools.base import BaseChatbotTool
from app.core.permissions import ViolationPermission
from app.core.principal import AuthPrincipal

# Descriptive catalog of business tables in dut-ai-manager
TABLE_DESCRIPTIONS: dict[str, str] = {
    "users": "Thông tin thành viên CLB/Lab (id, name, email, phone_number, status, check_in_card_code, discord_id...)",
    "roles": "Danh sách các vai trò quyền hạn trong hệ thống",
    "permissions": "Danh sách các mã quyền hạn RBAC",
    "user_roles": "Bảng liên kết giữa người dùng và vai trò",
    "meetings": "Danh sách các buổi học/sinh hoạt (id, title, start_time, end_time, evaluation_deadline...)",
    "meeting_participants": "Trạng thái tham gia, điểm danh và vai trò (Trainer, Trainee, Member) trong buổi học",
    "meeting_evaluations": "Đánh giá chi tiết của Trainer/Trainee sau buổi học",
    "meeting_overall_evaluations": "Bản đánh giá tổng quan buổi học",
    "homeworks": "Danh sách bài tập được giao (id, title, link, requires_coding, requires_game...)",
    "homework_assignees": "Phân công bài tập cho từng thành viên kèm hạn chót nộp bài (deadline) riêng biệt",
    "homework_submissions": "Lịch sử các lần nộp bài tập, điểm số và kết quả chấm bài",
    "violations": "Biên bản ghi nhận vi phạm kỷ luật (id, user_id, reason, date...)",
    "bonus_points": "Lịch sử điểm thưởng và đóng góp của thành viên (id, user_id, points, reason...)",
    "permission_requests": "Đơn xin phép (vắng họp, đi trễ, gia hạn bài tập) của thành viên",
    "teams": "Danh sách các nhóm/team hoạt động trong CLB/Lab",
    "team_members": "Danh sách thành viên thuộc các nhóm",
    "notifications": "Lịch sử thông báo hệ thống gửi đến người dùng",
}

EXCLUDED_TABLES: set[str] = {
    "alembic_version",
}


class DbListTablesTool(BaseChatbotTool):
    name = "db_list_tables"
    description = (
        "DÀNH CHO QUẢN TRỊ VIÊN/HR/MENTOR: Liệt kê danh sách tất cả các bảng dữ liệu trong hệ thống "
        "kèm mô tả nghiệp vụ ngắn gọn để xác định bảng cần tra cứu thông tin."
    )
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
    }
    required_permissions = [ViolationPermission.READ.value]

    def execute(
        self, session: Session, args: dict[str, Any], user: AuthPrincipal
    ) -> dict[str, Any]:
        engine = session.get_bind()
        inspector = inspect(engine)
        raw_table_names = inspector.get_table_names()

        tables_info = []
        for tbl in raw_table_names:
            if tbl in EXCLUDED_TABLES or tbl.startswith("celery_"):
                continue
            desc = TABLE_DESCRIPTIONS.get(tbl, f"Bảng dữ liệu {tbl}")
            tables_info.append({"name": tbl, "description": desc})

        return {
            "total_tables": len(tables_info),
            "tables": tables_info,
        }
