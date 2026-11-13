"""Unit tests for the Agent Domain Service."""

from collections.abc import AsyncGenerator
from typing import Any
from uuid import uuid4

import pytest

from app.chatbot.domain.agent import Agent
from app.chatbot.domain.entity import ChatMessage
from app.chatbot.domain.value_objects import MessageRole
from app.chatbot.infrastructure.tools_registry import ChatbotToolRegistry
from app.core.principal import AuthPrincipal, PrincipalType


class MockLLMClient:
    model = "mock-model"

    def __init__(self, responses: list[dict[str, Any]] | None = None) -> None:
        self.responses = responses or []
        self.call_count = 0

    async def count_tokens(self, messages: list[dict[str, Any]]) -> int:
        total_chars = sum(len(str(m.get("content") or "")) for m in messages)
        return max(1, total_chars // 4)

    async def stream_chat(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None, **kwargs: Any
    ) -> AsyncGenerator[dict[str, Any], None]:
        self.call_count += 1
        if self.call_count <= len(self.responses):
            chunks = self.responses[self.call_count - 1]
            for c in chunks:
                yield c
        else:
            yield {"type": "content", "data": "Default response"}


@pytest.mark.asyncio
async def test_agent_run_stream_emits_expected_events(db_session, mock_current_user):
    """Verify that Agent.run_stream emits iteration_step, reasoning, content, and complete event."""
    responses = [
        [
            {"type": "reasoning", "data": "Thinking process..."},
            {"type": "content", "data": "Xin chào, tôi là trợ lý DUT AI."},
            {"type": "usage", "data": {"usage": {"total_tokens": 42}, "timings": {"predicted_per_second": 100.0}}},
        ]
    ]
    mock_llm = MockLLMClient(responses)
    tool_registry = ChatbotToolRegistry(db_session)
    agent = Agent(llm_client=mock_llm, tool_registry=tool_registry, max_iterations=3)

    user = AuthPrincipal(
        actor_id=mock_current_user.id,
        actor_type=PrincipalType.USER,
        name=mock_current_user.name,
        email=mock_current_user.email,
        permissions=set(),
    )
    messages = [ChatMessage(session_id=uuid4(), role=MessageRole.USER, content="Xin chào")]

    events = [event async for event in agent.run_stream(messages, user)]
    event_types = [e.event_type for e in events]

    assert "iteration_step" in event_types
    assert "reasoning" in event_types
    assert "content" in event_types
    assert "complete" in event_types

    complete_event = next(e for e in events if e.event_type == "complete")
    assert complete_event.data["content"] == "Xin chào, tôi là trợ lý DUT AI."
    meta = complete_event.data["metadata"]
    assert meta.model_name == "mock-model"
    assert meta.reasoning_content == "Thinking process..."
    assert meta.usage == {"total_tokens": 42}


@pytest.mark.asyncio
async def test_agent_detects_duplicate_tool_calls(db_session, mock_current_user):
    """Verify Agent detects duplicate tool calls and skips duplicate execution."""
    responses = [
        # Turn 1: Call get_my_violations
        [
            {
                "type": "tool_calls_complete",
                "data": [{"id": "c1", "function": {"name": "get_my_violations", "arguments": "{}"}}],
            }
        ],
        # Turn 2: Attempt to call the exact same tool with identical arguments
        [
            {
                "type": "tool_calls_complete",
                "data": [{"id": "c2", "function": {"name": "get_my_violations", "arguments": "{}"}}],
            }
        ],
        # Turn 3: Deliver final answer
        [
            {"type": "content", "data": "Đã tổng hợp kết quả vi phạm."},
        ],
    ]
    mock_llm = MockLLMClient(responses)
    tool_registry = ChatbotToolRegistry(db_session)
    agent = Agent(llm_client=mock_llm, tool_registry=tool_registry, max_iterations=5)

    user = AuthPrincipal(
        actor_id=mock_current_user.id,
        actor_type=PrincipalType.USER,
        name=mock_current_user.name,
        email=mock_current_user.email,
        permissions=set(),
    )
    messages = [ChatMessage(session_id=uuid4(), role=MessageRole.USER, content="Kiểm tra vi phạm")]

    events = [event async for event in agent.run_stream(messages, user)]
    tool_end_events = [e for e in events if e.event_type == "tool_call_end"]
    assert len(tool_end_events) == 2
    assert tool_end_events[0].data["status"] == "success"
    assert tool_end_events[1].data["status"] == "duplicate_skipped"


@pytest.mark.asyncio
async def test_agent_context_pruning_only_on_threshold_overflow(db_session):
    """Verify that Agent context pruning triggers ONLY when token threshold is actually exceeded."""
    mock_llm = MockLLMClient()
    tool_registry = ChatbotToolRegistry(db_session)
    agent = Agent(llm_client=mock_llm, tool_registry=tool_registry)

    # 1. Under threshold -> No pruning
    messages_under = [
        {"role": "user", "content": "Hello"},
        {"role": "tool", "content": "A" * 1000},
    ]
    await agent.prune_context_if_needed(messages_under, max_threshold=5000)
    assert len(messages_under[1]["content"]) == 1000

    # 2. Exceeding threshold -> Pruned
    messages_over = [
        {"role": "user", "content": "Hello"},
        {"role": "tool", "content": "B" * 10000},
    ]
    await agent.prune_context_if_needed(messages_over, max_threshold=1000)
    assert "... [Dữ liệu đã được tóm tắt" in messages_over[1]["content"]


@pytest.mark.asyncio
async def test_agent_auto_nudges_when_promise_without_tool_call(db_session, mock_current_user):
    """Verify Agent detects promise without tool call, nudges the model, and completes execution."""
    responses = [
        # Turn 1: Model promises to look up but does NOT emit tool calls
        [
            {"type": "content", "data": "Vui lòng chờ một chút để tôi tra cứu thông tin này."},
        ],
        # Turn 2: After being nudged by system, model issues real tool call
        [
            {
                "type": "tool_calls_complete",
                "data": [{"id": "c1", "function": {"name": "get_my_violations", "arguments": "{}"}}],
            }
        ],
        # Turn 3: Model delivers final synthesized answer
        [
            {"type": "content", "data": "Dưới đây là kết quả tra cứu: Bạn có 0 vi phạm."},
        ],
    ]
    mock_llm = MockLLMClient(responses)
    tool_registry = ChatbotToolRegistry(db_session)
    agent = Agent(llm_client=mock_llm, tool_registry=tool_registry, max_iterations=5)

    user = AuthPrincipal(
        actor_id=mock_current_user.id,
        actor_type=PrincipalType.USER,
        name=mock_current_user.name,
        email=mock_current_user.email,
        permissions=set(),
    )
    messages = [ChatMessage(session_id=uuid4(), role=MessageRole.USER, content="Tra cứu cho tôi")]

    events = [event async for event in agent.run_stream(messages, user)]
    complete_event = next(e for e in events if e.event_type == "complete")
    assert "Dưới đây là kết quả tra cứu" in complete_event.data["content"]
    assert len(complete_event.data["metadata"].tools_invoked) == 1
    assert complete_event.data["metadata"].tools_invoked[0].tool_name == "get_my_violations"
