"""Tool to fetch detailed schema for a specific database table while masking sensitive columns."""

from typing import Any

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.chatbot.infrastructure.tools.base import BaseChatbotTool
from app.chatbot.infrastructure.tools.database.guard import SENSITIVE_COLUMNS
from app.core.permissions import ViolationPermission
from app.core.principal import AuthPrincipal


class DbGetTableSchemaTool(BaseChatbotTool):
    name = "db_get_table_schema"
    description = (
        "DÀNH CHO QUẢN TRỊ VIÊN/HR/MENTOR: Lấy thông tin chi tiết về các cột, kiểu dữ liệu, "
        "và khóa chính của một bảng cụ thể để chuẩn bị câu lệnh truy vấn dữ liệu."
    )
    parameters = {
        "type": "object",
        "properties": {
            "table_name": {
                "type": "string",
                "description": "Tên bảng cần xem schema chi tiết (ví dụ: 'users', 'violations', 'meetings').",
            }
        },
        "required": ["table_name"],
    }
    required_permissions = [ViolationPermission.READ.value]

    def execute(
        self, session: Session, args: dict[str, Any], user: AuthPrincipal
    ) -> dict[str, Any]:
        table_name = args.get("table_name", "").strip().lower()
        if not table_name:
            return {"error": "Vui lòng cung cấp tên bảng cần xem schema."}

        engine = session.get_bind()
        inspector = inspect(engine)

        if not inspector.has_table(table_name):
            return {"error": f"Không tìm thấy bảng '{table_name}' trong cơ sở dữ liệu."}

        pk_constraint = inspector.get_pk_constraint(table_name)
        pk_columns = pk_constraint.get("constrained_columns", [])

        columns_meta = []
        for col in inspector.get_columns(table_name):
            col_name = col.get("name", "")
            # Strict security: Mask sensitive credentials columns
            if col_name.lower() in SENSITIVE_COLUMNS:
                continue

            columns_meta.append({
                "name": col_name,
                "type": str(col.get("type")),
                "nullable": col.get("nullable", True),
                "is_primary_key": col_name in pk_columns,
            })

        return {
            "table_name": table_name,
            "primary_key": pk_columns,
            "total_columns": len(columns_meta),
            "columns": columns_meta,
        }
