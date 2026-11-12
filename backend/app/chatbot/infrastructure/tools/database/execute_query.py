"""Tool to safely execute read-only SELECT queries on the PostgreSQL database."""

from datetime import date, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.chatbot.infrastructure.tools.base import BaseChatbotTool
from app.chatbot.infrastructure.tools.database.guard import (
    SqlSafetyGuard,
    SqlSecurityError,
)
from app.core.permissions import ViolationPermission
from app.core.principal import AuthPrincipal


def _serialize_row_value(val: Any) -> Any:
    """Serializes date/datetime or complex types into JSON-safe formats."""
    if isinstance(val, (datetime, date)):
        return val.strftime("%d/%m/%Y %H:%M") if isinstance(val, datetime) else val.strftime("%d/%m/%Y")
    return val


class DbExecuteQueryTool(BaseChatbotTool):
    name = "db_execute_query"
    description = (
        "DÀNH CHO QUẢN TRỊ VIÊN/HR/MENTOR: Thực thi câu lệnh SQL SELECT an toàn trên database "
        "để tra cứu, lọc hoặc tính toán thống kê dữ liệu. Tuyệt đối chỉ nhận câu lệnh SELECT hoặc WITH."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Câu lệnh SQL SELECT cần thực thi (ví dụ: 'SELECT u.name, v.date, v.reason FROM violations v JOIN users u ON u.id = v.user_id WHERE u.name ILIKE \'%Nguyễn Lê Vy%\' ORDER BY v.date DESC').",
            }
        },
        "required": ["query"],
    }
    required_permissions = [ViolationPermission.READ.value]

    def execute(
        self, session: Session, args: dict[str, Any], user: AuthPrincipal
    ) -> dict[str, Any]:
        raw_query = args.get("query", "").strip()
        if not raw_query:
            return {"error": "Vui lòng cung cấp câu lệnh SQL cần thực thi."}

        try:
            # Enforce read-only keywords, sensitive column masking, and automatic LIMIT 50
            safe_sql = SqlSafetyGuard.validate_and_format_query(raw_query)
        except SqlSecurityError as e:
            return {"error": f"Lỗi kiểm tra bảo mật truy vấn: {str(e)}"}

        try:
            # Execute within a nested transaction (savepoint) so failures rollback cleanly
            # and do not corrupt the outer request transaction (preventing InFailedSqlTransaction)
            with session.begin_nested():
                # Set statement timeout to 5 seconds to prevent runaway queries if supported (PostgreSQL)
                try:
                    session.execute(text("SET LOCAL statement_timeout = 5000;"))
                except Exception:
                    pass

                result = session.execute(text(safe_sql))
                column_names = list(result.keys())
                rows = result.fetchall()

                serialized_rows = [
                    {col: _serialize_row_value(val) for col, val in zip(column_names, row, strict=False)}
                    for row in rows
                ]

                return {
                    "executed_query": safe_sql,
                    "row_count": len(serialized_rows),
                    "columns": column_names,
                    "rows": serialized_rows,
                }
        except Exception as ex:
            return {
                "status": "FAILED",
                "error": f"Lỗi thực thi cơ sở dữ liệu: {str(ex)}",
                "instruction": (
                    "TRUY VẤN SQL THẤT BẠI. Dữ liệu chưa được lấy thành công. "
                    "BẠN TUYỆT ĐỐI KHÔNG ĐƯỢC BỊA ĐẶT DỮ LIỆU HOẶC TỰ KẾT THÚC CÂU TRẢ LỜI. "
                    "Hãy đọc kỹ thông báo lỗi ở trên, gọi `db_get_table_schema` nếu cần kiểm tra lại tên cột/kiểu dữ liệu, "
                    "và viết lại câu lệnh SQL chính xác để thực thi lại."
                ),
            }
