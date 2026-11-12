"""Tool to inspect foreign key relationships and generate JOIN hints between tables."""

from typing import Any

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.chatbot.infrastructure.tools.base import BaseChatbotTool
from app.core.permissions import ViolationPermission
from app.core.principal import AuthPrincipal


class DbGetTableRelationshipsTool(BaseChatbotTool):
    name = "db_get_table_relationships"
    description = (
        "DÀNH CHO QUẢN TRỊ VIÊN/HR/MENTOR: Xem sơ đồ liên kết khóa ngoại (Foreign Keys) "
        "giữa các bảng để biết cách viết câu lệnh JOIN chính xác khi kết hợp dữ liệu nhiều bảng."
    )
    parameters = {
        "type": "object",
        "properties": {
            "tables": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Danh sách các bảng cần kiểm tra quan hệ (ví dụ: ['users', 'violations'] hoặc ['meetings', 'meeting_participants']).",
            }
        },
        "required": ["tables"],
    }
    required_permissions = [ViolationPermission.READ.value]

    def execute(
        self, session: Session, args: dict[str, Any], user: AuthPrincipal
    ) -> dict[str, Any]:
        tables = [str(t).strip().lower() for t in args.get("tables", []) if t]
        if not tables:
            return {"error": "Vui lòng cung cấp danh sách bảng cần kiểm tra quan hệ."}

        engine = session.get_bind()
        inspector = inspect(engine)

        relationships = []
        tables_set = set(tables)

        for src_tbl in tables:
            if not inspector.has_table(src_tbl):
                continue

            fks = inspector.get_foreign_keys(src_tbl)
            for fk in fks:
                referred_table = fk.get("referred_table", "")
                constrained_cols = fk.get("constrained_columns", [])
                referred_cols = fk.get("referred_columns", [])

                if not constrained_cols or not referred_cols:
                    continue

                src_col = constrained_cols[0]
                target_col = referred_cols[0]

                # Direct relationship between the requested tables
                if referred_table in tables_set:
                    relationships.append({
                        "source_table": src_tbl,
                        "source_column": src_col,
                        "target_table": referred_table,
                        "target_column": target_col,
                        "join_hint": f"JOIN {referred_table} ON {referred_table}.{target_col} = {src_tbl}.{src_col}",
                    })
                elif len(tables_set) == 1:
                    # If user asked for relationships of just 1 table, list all outgoing references
                    relationships.append({
                        "source_table": src_tbl,
                        "source_column": src_col,
                        "target_table": referred_table,
                        "target_column": target_col,
                        "join_hint": f"JOIN {referred_table} ON {referred_table}.{target_col} = {src_tbl}.{src_col}",
                    })

        return {
            "checked_tables": tables,
            "relationships_found": len(relationships),
            "relationships": relationships,
        }
