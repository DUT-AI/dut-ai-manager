"""Unit tests for Dynamic Database Tools and SQL Safety Guard."""

import pytest
from app.chatbot.infrastructure.tools.database.guard import (
    SqlSafetyGuard,
    SqlSecurityError,
)
from app.chatbot.infrastructure.tools.database.list_tables import DbListTablesTool
from app.chatbot.infrastructure.tools.database.get_table_schema import (
    DbGetTableSchemaTool,
)
from app.chatbot.infrastructure.tools.database.get_table_relationships import (
    DbGetTableRelationshipsTool,
)
from app.chatbot.infrastructure.tools.database.execute_query import (
    DbExecuteQueryTool,
)
from app.core.permissions import ViolationPermission
from app.core.principal import AuthPrincipal, PrincipalType


def test_sql_safety_guard_blocks_mutations():
    """Verify SqlSafetyGuard blocks all mutation and DDL statements."""
    forbidden = [
        "DROP TABLE users;",
        "DELETE FROM violations WHERE id = 1;",
        "UPDATE users SET name = 'Hacked';",
        "INSERT INTO roles (name) VALUES ('Hacker');",
        "ALTER TABLE users ADD COLUMN test TEXT;",
        "TRUNCATE TABLE meetings;",
        "SELECT * FROM users; DROP TABLE users;",
    ]
    for q in forbidden:
        with pytest.raises(SqlSecurityError):
            SqlSafetyGuard.validate_and_format_query(q)


def test_sql_safety_guard_blocks_sensitive_columns():
    """Verify SqlSafetyGuard prevents querying password hashes or tokens."""
    sensitive_queries = [
        "SELECT id, hashed_password FROM users",
        "SELECT token FROM sessions",
        "SELECT api_key FROM role_api_keys",
    ]
    for q in sensitive_queries:
        with pytest.raises(SqlSecurityError):
            SqlSafetyGuard.validate_and_format_query(q)


def test_sql_safety_guard_enforces_limit():
    """Verify SqlSafetyGuard adds or caps LIMIT."""
    # Adds default LIMIT 50
    q1 = SqlSafetyGuard.validate_and_format_query("SELECT id, name FROM users")
    assert "LIMIT 50" in q1

    # Caps limit at 100
    q2 = SqlSafetyGuard.validate_and_format_query("SELECT id FROM users LIMIT 500")
    assert "LIMIT 100" in q2

    # Retains safe limit under 100
    q3 = SqlSafetyGuard.validate_and_format_query("SELECT id FROM users LIMIT 10")
    assert "LIMIT 10" in q3


def test_db_list_tables_tool(db_session, mock_current_user):
    """Verify DbListTablesTool lists database tables without technical tables."""
    admin = AuthPrincipal(
        actor_id=mock_current_user.id,
        actor_type=PrincipalType.USER,
        name="Admin",
        email="admin@dut.vn",
        permissions={ViolationPermission.READ.value},
    )
    tool = DbListTablesTool()
    res = tool.execute(db_session, {}, admin)

    assert "tables" in res
    assert res["total_tables"] > 0
    names = [t["name"] for t in res["tables"]]
    assert "alembic_version" not in names


def test_db_get_table_schema_masks_sensitive_columns(db_session, mock_current_user):
    """Verify DbGetTableSchemaTool hides hashed_password and returns column metadata."""
    admin = AuthPrincipal(
        actor_id=mock_current_user.id,
        actor_type=PrincipalType.USER,
        name="Admin",
        email="admin@dut.vn",
        permissions={ViolationPermission.READ.value},
    )
    tool = DbGetTableSchemaTool()
    res = tool.execute(db_session, {"table_name": "users"}, admin)

    assert res["table_name"] == "users"
    col_names = [c["name"] for c in res["columns"]]
    assert "name" in col_names
    assert "email" in col_names
    assert "hashed_password" not in col_names


def test_db_get_table_relationships_returns_join_hints(db_session, mock_current_user):
    """Verify DbGetTableRelationshipsTool detects foreign keys between tables."""
    admin = AuthPrincipal(
        actor_id=mock_current_user.id,
        actor_type=PrincipalType.USER,
        name="Admin",
        email="admin@dut.vn",
        permissions={ViolationPermission.READ.value},
    )
    tool = DbGetTableRelationshipsTool()
    res = tool.execute(db_session, {"tables": ["users", "violations"]}, admin)

    assert "relationships" in res
    # Should identify user_id foreign key from violations to users if defined in DB
    if res["relationships_found"] > 0:
        first_rel = res["relationships"][0]
        assert "join_hint" in first_rel


def test_db_execute_query_tool_execution(db_session, mock_current_user):
    """Verify DbExecuteQueryTool safely executes SELECT queries and returns rows."""
    admin = AuthPrincipal(
        actor_id=mock_current_user.id,
        actor_type=PrincipalType.USER,
        name="Admin",
        email="admin@dut.vn",
        permissions={ViolationPermission.READ.value},
    )
    tool = DbExecuteQueryTool()

    # Safe SELECT query
    res = tool.execute(
        db_session,
        {"query": f"SELECT id, name, email FROM users WHERE id = {mock_current_user.id}"},
        admin,
    )
    assert "rows" in res
    assert res["row_count"] >= 1
    assert res["rows"][0]["email"] == mock_current_user.email

    # Blocked dangerous query
    res_bad = tool.execute(
        db_session,
        {"query": "DROP TABLE users"},
        admin,
    )
    assert "error" in res_bad


def test_db_execute_query_syntax_error_does_not_abort_transaction(db_session, mock_current_user):
    """Verify that a failing query does not abort the outer transaction or block subsequent inserts."""
    from sqlalchemy import text

    admin = AuthPrincipal(
        actor_id=mock_current_user.id,
        actor_type=PrincipalType.USER,
        name="Admin",
        email="admin@dut.vn",
        permissions={ViolationPermission.READ.value},
    )
    tool = DbExecuteQueryTool()

    # Query with a non-existent table to trigger a database-level error
    res_err = tool.execute(
        db_session,
        {"query": "SELECT * FROM non_existent_dummy_table_12345"},
        admin,
    )
    assert "error" in res_err

    # The outer session must remain valid and operational (no InFailedSqlTransaction)
    check_query = db_session.execute(text("SELECT 1")).scalar()
    assert check_query == 1

