"""Unit tests for Chatbot domain, repository FIFO pruning, and tool RBAC security."""

from app.chatbot.domain.entity import ChatSession
from app.chatbot.infrastructure.repository import ChatRepository
from app.chatbot.infrastructure.tools_registry import ChatbotToolRegistry
from app.core.permissions import ViolationPermission
from app.core.principal import AuthPrincipal, PrincipalType


def test_chat_session_title_truncation():
    """Verify title generation truncates to 50 characters with ellipsis."""
    session = ChatSession(user_id=1)
    long_msg = "A" * 70
    session.update_title_from_first_message(long_msg)
    assert len(session.title) == 53
    assert session.title.endswith("...")


def test_chat_repository_fifo_pruning(db_session, mock_current_user):
    """Verify that user cannot have more than 5 chat sessions (FIFO pruning)."""
    repo = ChatRepository(db_session)
    user_id = mock_current_user.id

    # Clean any prior sessions for this user_id
    sessions = repo.get_user_sessions(user_id)
    for s in sessions:
        repo.delete_session(s.id, user_id)

    # Create 5 sessions
    created_sessions = []
    for i in range(1, 6):
        sess = repo.create_session(ChatSession(user_id=user_id, title=f"Session {i}"))
        created_sessions.append(sess)

    assert len(repo.get_user_sessions(user_id)) == 5
    first_session_id = created_sessions[0].id

    # Create the 6th session -> Should prune the 1st session
    sess6 = repo.create_session(ChatSession(user_id=user_id, title="Session 6"))

    active_sessions = repo.get_user_sessions(user_id)
    assert len(active_sessions) == 5
    active_ids = [s.id for s in active_sessions]
    assert first_session_id not in active_ids
    assert sess6.id in active_ids

    # Cleanup
    for s in active_sessions:
        repo.delete_session(s.id, user_id)


def test_chatbot_tools_rbac_security(db_session):
    """Verify that regular member cannot execute admin tools."""
    registry = ChatbotToolRegistry(db_session)

    # 1. Normal member without admin permissions
    member = AuthPrincipal(
        actor_id=1,
        actor_type=PrincipalType.USER,
        name="Member",
        email="member@dut.vn",
        permissions=set(),
    )
    member_tools = registry.get_tool_definitions(member)
    tool_names = [t["function"]["name"] for t in member_tools]
    assert "get_my_violations" in tool_names
    assert "get_violation_policies" in tool_names
    assert "admin_summarize_violations" not in tool_names

    # Trying to execute admin tool anyway should be blocked
    res = registry.execute_tool("admin_summarize_violations", {}, member)
    assert "error" in res

    # 2. Admin with ViolationPermission.READ
    admin = AuthPrincipal(
        actor_id=2,
        actor_type=PrincipalType.USER,
        name="Admin",
        email="admin@dut.vn",
        permissions={ViolationPermission.READ.value},
    )
    admin_tools = registry.get_tool_definitions(admin)
    admin_tool_names = [t["function"]["name"] for t in admin_tools]
    assert "admin_summarize_violations" in admin_tool_names


def test_custom_tool_extensibility(db_session):
    """Verify Open-Closed Principle: custom tools can be registered without altering registry code."""
    from typing import Any

    from sqlalchemy.orm import Session

    from app.chatbot.infrastructure.tools.base import BaseChatbotTool

    class WeatherTool(BaseChatbotTool):
        name = "get_weather_forecast"
        description = "Dự báo thời tiết."
        parameters = {"type": "object", "properties": {"city": {"type": "string"}}}
        required_permissions = []

        def execute(self, session: Session, args: dict[str, Any], user: AuthPrincipal) -> dict[str, Any]:
            return {"city": args.get("city", "Da Nang"), "status": "Sunny"}

    registry = ChatbotToolRegistry(db_session)
    weather_tool = WeatherTool()
    registry.register(weather_tool)

    user = AuthPrincipal(
        actor_id=1,
        actor_type=PrincipalType.USER,
        name="Member",
        email="member@dut.vn",
        permissions=set(),
    )

    tools = registry.get_tool_definitions(user)
    tool_names = [t["function"]["name"] for t in tools]
    assert "get_weather_forecast" in tool_names

    result = registry.execute_tool("get_weather_forecast", {"city": "Hue"}, user)
    assert result == {"city": "Hue", "status": "Sunny"}


def test_admin_get_meeting_absentees_returns_user_details(db_session, mock_current_user):
    """Verify AdminGetMeetingAbsenteesTool returns full user details (name, email) instead of raw IDs."""
    from app.core.permissions import MeetingPermission
    from app.meeting.domain.value_objects import ParticipantStatus
    from app.meeting.infrastructure.model import Meeting, MeetingParticipant
    from app.chatbot.infrastructure.tools.admin.meeting_absentees import AdminGetMeetingAbsenteesTool
    from datetime import datetime, UTC

    # Setup meeting and participant
    meeting = Meeting(
        title="Test Sinh Hoạt",
        start_time=datetime.now(UTC),
        end_time=datetime.now(UTC),
        evaluation_deadline=datetime.now(UTC),
    )
    db_session.add(meeting)
    db_session.flush()

    participant = MeetingParticipant(
        meeting_id=meeting.id,
        user_id=mock_current_user.id,
        status=ParticipantStatus.ABSENT_UNEXCUSED.value,
        role="MEMBER",
    )
    db_session.add(participant)
    db_session.flush()

    admin = AuthPrincipal(
        actor_id=mock_current_user.id,
        actor_type=PrincipalType.USER,
        name="Admin",
        email="admin@dut.vn",
        permissions={MeetingPermission.READ.value},
    )

    tool = AdminGetMeetingAbsenteesTool()
    res = tool.execute(db_session, {}, admin)

    assert "absentees" in res
    assert res["absentee_count"] >= 1
    first_absentee = res["absentees"][0]
    assert first_absentee["user_id"] == mock_current_user.id
    assert first_absentee["name"] == mock_current_user.name
    assert first_absentee["email"] == mock_current_user.email


def test_admin_get_unsubmitted_homeworks_tool(db_session, mock_current_user):
    """Verify AdminGetUnsubmittedHomeworksTool uses individual assignee deadlines and does not crash on hw.deadline."""
    from datetime import datetime, UTC
    from app.core.permissions import HomeworkPermission
    from app.homework.infrastructure.model import (
        HomeworkAssigneeModel,
        HomeworkModel,
    )
    from app.chatbot.infrastructure.tools.admin.unsubmitted_homeworks import (
        AdminGetUnsubmittedHomeworksTool,
    )

    hw = HomeworkModel(
        title="Bài tập Python Cơ Bản",
        requires_coding=True,
    )
    db_session.add(hw)
    db_session.flush()

    assignee = HomeworkAssigneeModel(
        homework_id=hw.id,
        user_id=mock_current_user.id,
        deadline=datetime.now(UTC),
    )
    db_session.add(assignee)
    db_session.flush()

    admin = AuthPrincipal(
        actor_id=mock_current_user.id,
        actor_type=PrincipalType.USER,
        name="Admin",
        email="admin@dut.vn",
        permissions={HomeworkPermission.READ.value},
    )

    tool = AdminGetUnsubmittedHomeworksTool()
    res = tool.execute(db_session, {"homework_title": "Python"}, admin)

    assert res["homework_id"] == hw.id
    assert res["homework_title"] == "Bài tập Python Cơ Bản"
    assert res["deadline"] is not None
    assert res["unsubmitted_count"] == 1
    assert res["unsubmitted_members"][0]["user_id"] == mock_current_user.id
    assert res["unsubmitted_members"][0]["deadline"] is not None



