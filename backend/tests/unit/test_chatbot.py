"""Unit tests for Chatbot domain, repository FIFO pruning, and tool RBAC security."""

import pytest

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
    """Verify that regular member cannot execute admin database tools."""
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
    assert "db_execute_query" not in tool_names
    assert "db_list_tables" not in tool_names

    # Trying to execute admin tool anyway should be blocked
    res = registry.execute_tool("db_execute_query", {"query": "SELECT * FROM users"}, member)
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
    assert "db_execute_query" in admin_tool_names
    assert "db_list_tables" in admin_tool_names


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


@pytest.mark.asyncio
async def test_agent_loop_multi_step_tool_chaining(db_session, mock_current_user):
    """Verify that SendChatMessageUseCase executes multiple tool turns (Agent Loop) in a single message."""
    from collections.abc import AsyncGenerator
    from typing import Any
    from app.chatbot.application.send_chat_message_use_case import SendChatMessageUseCase
    from app.chatbot.domain.value_objects import ToolCallRecord

    class MockMultiStepLLMClient:
        model = "mock-model"

        def __init__(self):
            self.call_count = 0

        async def stream_chat(
            self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None, **kwargs
        ) -> AsyncGenerator[dict[str, Any], None]:
            self.call_count += 1
            if self.call_count == 1:
                # First turn: model decides to call tool 1
                yield {"type": "reasoning", "data": "Checking tool 1..."}
                yield {
                    "type": "tool_calls_complete",
                    "data": [
                        {
                            "id": "call_1",
                            "function": {"name": "get_violation_policies", "arguments": "{}"},
                        }
                    ],
                }
            elif self.call_count == 2:
                # Second turn: model sees tool 1 result, now calls tool 2
                yield {"type": "reasoning", "data": "Now checking my violations..."}
                yield {
                    "type": "tool_calls_complete",
                    "data": [
                        {
                            "id": "call_2",
                            "function": {"name": "get_my_violations", "arguments": "{}"},
                        }
                    ],
                }
            else:
                # Third turn: model delivers final answer
                yield {"type": "content", "data": "Bạn có 0 vi phạm theo chính sách."}

    mock_llm = MockMultiStepLLMClient()
    repo = ChatRepository(db_session)
    registry = ChatbotToolRegistry(db_session)
    use_case = SendChatMessageUseCase(repo=repo, llm_client=mock_llm, tool_registry=registry)

    user = AuthPrincipal(
        actor_id=mock_current_user.id,
        actor_type=PrincipalType.USER,
        name=mock_current_user.name,
        email=mock_current_user.email,
        permissions=set(),
    )

    chunks = []
    async for chunk in use_case.execute("Kiểm tra chính sách và vi phạm của tôi", None, user):
        chunks.append(chunk)

    full_stream = "".join(chunks)
    assert 'type": "iteration_step", "data": {"iteration": 1' in full_stream
    assert 'type": "iteration_step", "data": {"iteration": 2' in full_stream
    assert 'type": "iteration_step", "data": {"iteration": 3' in full_stream
    assert "Bạn có 0 vi phạm theo chính sách." in full_stream

    # Check that both tools were recorded in assistant message metadata
    sessions = repo.get_user_sessions(mock_current_user.id)
    assert len(sessions) > 0
    latest_session_id = sessions[0].id
    messages = repo.get_session_messages(latest_session_id, mock_current_user.id)
    assistant_msg = messages[-1]
    assert assistant_msg.role.value == "assistant"
    assert len(assistant_msg.metadata_info.tools_invoked) == 2
    assert assistant_msg.metadata_info.tools_invoked[0].tool_name == "get_violation_policies"
    assert assistant_msg.metadata_info.tools_invoked[1].tool_name == "get_my_violations"


@pytest.mark.asyncio
async def test_agent_loop_duplicate_tool_call_prevention(db_session, mock_current_user):
    """Verify that Agent Loop detects duplicate tool calls and skips redundant execution."""
    from collections.abc import AsyncGenerator
    from typing import Any
    from app.chatbot.application.send_chat_message_use_case import SendChatMessageUseCase

    class MockLoopingLLMClient:
        model = "mock-model"

        def __init__(self):
            self.call_count = 0

        async def stream_chat(
            self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None, **kwargs
        ) -> AsyncGenerator[dict[str, Any], None]:
            self.call_count += 1
            if self.call_count == 1:
                # Turn 1: Call get_my_violations
                yield {
                    "type": "tool_calls_complete",
                    "data": [{"id": "c1", "function": {"name": "get_my_violations", "arguments": "{}"}}],
                }
            elif self.call_count == 2:
                # Turn 2: Attempt to call the exact same tool with identical arguments
                yield {
                    "type": "tool_calls_complete",
                    "data": [{"id": "c2", "function": {"name": "get_my_violations", "arguments": "{}"}}],
                }
            else:
                yield {"type": "content", "data": "Đã tổng hợp xong."}

    mock_llm = MockLoopingLLMClient()
    repo = ChatRepository(db_session)
    registry = ChatbotToolRegistry(db_session)
    use_case = SendChatMessageUseCase(repo=repo, llm_client=mock_llm, tool_registry=registry)

    user = AuthPrincipal(
        actor_id=mock_current_user.id,
        actor_type=PrincipalType.USER,
        name=mock_current_user.name,
        email=mock_current_user.email,
        permissions=set(),
    )

    chunks = [c async for c in use_case.execute("Kiểm tra lặp", None, user)]
    full_stream = "".join(chunks)

    # Check tool status reported duplicate_skipped
    assert 'status": "duplicate_skipped"' in full_stream


@pytest.mark.asyncio
async def test_agent_loop_context_pruning_only_on_threshold_overflow(db_session):
    """Verify that context pruning triggers ONLY when token threshold is actually exceeded."""
    from app.chatbot.application.send_chat_message_use_case import SendChatMessageUseCase

    use_case = SendChatMessageUseCase(repo=None, llm_client=None, tool_registry=None)

    # Normal message under threshold -> No pruning
    messages_under = [
        {"role": "user", "content": "Hello"},
        {"role": "tool", "content": "A" * 1000},
    ]
    await use_case._prune_context_history_if_needed(messages_under, max_threshold=5000)
    assert len(messages_under[1]["content"]) == 1000

    # Oversized message exceeding threshold -> Pruned
    messages_over = [
        {"role": "user", "content": "Hello"},
        {"role": "tool", "content": "B" * 10000},
    ]
    await use_case._prune_context_history_if_needed(messages_over, max_threshold=1000)
    assert "... [Dữ liệu đã được tóm tắt" in messages_over[1]["content"]


@pytest.mark.asyncio
async def test_agent_dynamic_database_query_e2e(db_session, mock_current_user):
    """Verify Agent Loop performs progressive discovery and executes read-only SQL for specific user queries."""
    from collections.abc import AsyncGenerator
    from typing import Any
    from app.chatbot.application.send_chat_message_use_case import SendChatMessageUseCase

    class MockSqlAgentLLMClient:
        model = "mock-model"

        def __init__(self):
            self.turn = 0

        async def stream_chat(
            self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None, **kwargs
        ) -> AsyncGenerator[dict[str, Any], None]:
            self.turn += 1
            if self.turn == 1:
                # Agent inspects relationships between users and violations
                yield {
                    "type": "tool_calls_complete",
                    "data": [
                        {
                            "id": "c1",
                            "function": {
                                "name": "db_get_table_relationships",
                                "arguments": '{"tables": ["users", "violations"]}',
                            },
                        }
                    ],
                }
            elif self.turn == 2:
                # Agent executes SQL query using JOIN
                yield {
                    "type": "tool_calls_complete",
                    "data": [
                        {
                            "id": "c2",
                            "function": {
                                "name": "db_execute_query",
                                "arguments": (
                                    '{"query": "SELECT u.name, v.reason, v.date '
                                    'FROM violations v JOIN users u ON u.id = v.user_id '
                                    f'WHERE u.id = {mock_current_user.id}"}}'
                                ),
                            },
                        }
                    ],
                }
            else:
                # Agent produces formatted summary
                yield {"type": "content", "data": "Dưới đây là danh sách vi phạm của bạn."}

    mock_llm = MockSqlAgentLLMClient()
    repo = ChatRepository(db_session)
    registry = ChatbotToolRegistry(db_session)
    use_case = SendChatMessageUseCase(repo=repo, llm_client=mock_llm, tool_registry=registry)

    admin = AuthPrincipal(
        actor_id=mock_current_user.id,
        actor_type=PrincipalType.USER,
        name="Admin",
        email="admin@dut.vn",
        permissions={ViolationPermission.READ.value},
    )

    chunks = [c async for c in use_case.execute("Liệt kê vi phạm của user", None, admin)]
    full_output = "".join(chunks)

    assert "db_get_table_relationships" in full_output
    assert "db_execute_query" in full_output
    assert "Dưới đây là danh sách vi phạm của bạn." in full_output





