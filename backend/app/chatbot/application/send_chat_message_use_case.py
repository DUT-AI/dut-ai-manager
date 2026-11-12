"""Use Case to orchestrate sending chat messages, invoking tools, and streaming SSE responses via an Agent Loop."""

import json
from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

from app.chatbot.domain.entity import ChatMessage, ChatSession
from app.chatbot.domain.value_objects import (
    AgentLoopState,
    ChatMessageMetadata,
    MessageRole,
    ToolCallRecord,
)
from app.chatbot.infrastructure.llm_client import LLMClient
from app.chatbot.infrastructure.repository import ChatRepository
from app.chatbot.infrastructure.tools_registry import ChatbotToolRegistry
from app.core.config import settings
from app.core.principal import AuthPrincipal

SYSTEM_PROMPT = """
Bạn là DUT AI Assistant - Trợ lý thông minh giải đáp vi phạm và điều hành học vụ của CLB/Lab DUT AI.

NGUYÊN TẮC BẮT BUỘC (CRITICAL MANDATES):
1. Luôn trả lời bằng TIẾNG VIỆT lịch sự, rõ ràng, định dạng Markdown (tiêu đề, danh sách, bảng Markdown, in đậm từ khóa).

2. CHỐNG BỊA ĐẶT DỮ LIỆU (ANTI-HALLUCINATION PROTOCOL):
   - Tuyệt đối không được bịa đặt tên người, ngày giờ, số liệu hoặc bất kỳ bản ghi vi phạm/bài tập/buổi họp nào nếu chưa truy vấn thành công từ database.
   - Nếu truy vấn SQL thất bại hoặc gặp lỗi (error), bạn KHÔNG ĐƯỢC PHÉP tự sáng tác kết quả mẫu (ví dụ: Nguyễn Văn A, Trần Thị B...) để trả lời người dùng. Làm như vậy là vi phạm nghiêm trọng!

3. CƠ CHẾ TỰ SỬA LỖI TRUY VẤN (SQL SELF-CORRECTION & REFLECTION):
   - Khi một công cụ (đặc biệt là db_execute_query) trả về thông báo lỗi (status: FAILED hoặc có error):
     + BẠN PHẢI TIẾP TỤC VÒNG LẶP SUY LUẬN ĐỂ SỬA LỖI, KHÔNG ĐƯỢC DỪNG LẠI.
     + Phân tích xem lỗi do đâu: thiếu bảng, sai tên cột, sai kiểu dữ liệu, hay thiếu điều kiện JOIN.
     + Nếu không chắc chắn về tên cột: Hãy gọi db_get_table_schema(table_name=...) để xem chính xác các cột thực tế của bảng.
     + Nếu không chắc về khóa ngoại để JOIN: Hãy gọi db_get_table_relationships(tables=[...]).
     + Sau đó viết lại câu lệnh SQL chuẩn xác và gọi lại db_execute_query.

4. QUY TRÌNH TRUY VẤN DATABASE LINH HOẠT (PROGRESSIVE DATABASE DISCOVERY):
   - Khi cần tra cứu thông tin (danh sách vi phạm, thành viên, bài tập, buổi họp):
     + Bước 1: Gọi db_list_tables nếu cần biết các bảng liên quan.
     + Bước 2: Gọi db_get_table_schema hoặc db_get_table_relationships để xác định cấu trúc cột và liên kết khóa ngoại.
     + Bước 3: Viết câu lệnh SQL SELECT (kèm JOIN, WHERE, ORDER BY nếu cần) và thực thi qua db_execute_query.
     + Bước 4: Khi nhận được kết quả rows từ database, định dạng thành bảng Markdown chuyên nghiệp để trả lời người dùng.

5. NGUYÊN TẮC TRÌNH BÀY DANH SÁCH:
   - Khi hiển thị danh sách người dùng/vi phạm, LUÔN định dạng BẢNG MARKDOWN: | STT | Họ và Tên | Email/Ngày | Nội dung |.
   - TUYỆT ĐỐI KHÔNG in danh sách chỉ có mỗi số ID vô nghĩa.
"""


class SendChatMessageUseCase:
    """Orchestrates LLM interaction, session management, and SSE streaming."""

    def __init__(
        self,
        repo: ChatRepository,
        llm_client: LLMClient,
        tool_registry: ChatbotToolRegistry,
    ) -> None:
        self.repo = repo
        self.llm_client = llm_client
        self.tool_registry = tool_registry

    def _resolve_session(
        self, session_id: UUID | None, user_id: int, message: str
    ) -> tuple[ChatSession, bool]:
        if session_id:
            if existing := self.repo.get_session_by_id(session_id, user_id):
                return existing, False

        new_session = ChatSession(user_id=user_id)
        new_session.update_title_from_first_message(message)
        return self.repo.create_session(new_session), True

    def _build_llm_messages(
        self, recent_history: list[ChatMessage]
    ) -> list[dict[str, Any]]:
        llm_messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        for msg in recent_history:
            llm_messages.append({"role": msg.role.value, "content": msg.content})
        return llm_messages

    def _estimate_tokens(self, messages: list[dict[str, Any]]) -> int:
        """Rough token count estimation (~4 characters per token)."""
        total_chars = sum(len(str(m.get("content") or "")) for m in messages)
        return total_chars // 4

    def _prune_context_history_if_needed(
        self,
        llm_messages: list[dict[str, Any]],
        max_threshold: int = settings.CHATBOT_PRUNE_TOKEN_THRESHOLD,
    ) -> None:
        """Prunes historical tool results only when total context exceeds the safe threshold (e.g. 50k tokens)."""
        current_tokens = self._estimate_tokens(llm_messages)
        if current_tokens < max_threshold:
            return

        # Find older tool messages and compress/prune their content
        for msg in llm_messages:
            if msg.get("role") == "tool" and len(str(msg.get("content") or "")) > 300:
                raw_content = str(msg.get("content") or "")
                msg["content"] = raw_content[:250] + "... [Dữ liệu đã được tóm tắt để tối ưu bộ nhớ context]"
                if self._estimate_tokens(llm_messages) < max_threshold:
                    break

    def _execute_tools(
        self,
        pending_tool_calls: list[dict[str, Any]],
        user: AuthPrincipal,
        llm_messages: list[dict[str, Any]],
        loop_state: AgentLoopState,
    ) -> list[tuple[str, str, dict[str, Any]]]:
        """Executes pending tools with infinite loop prevention and records them into loop_state.

        Returns list of (tool_name, status, args) for SSE events.
        """
        events: list[tuple[str, str, dict[str, Any]]] = []
        for tc in pending_tool_calls:
            func_info = tc.get("function", {})
            tool_name = func_info.get("name", "")
            args_raw = func_info.get("arguments", "{}")
            try:
                args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
            except Exception:
                args = {}

            # US2: Detect duplicate tool calls in the same loop
            is_new_call = loop_state.add_call_signature(tool_name, args)
            if not is_new_call:
                tool_result = {
                    "warning": (
                        f"Công cụ '{tool_name}' đã được gọi trước đó với cùng tham số. "
                        "Vui lòng không gọi lại mà hãy sử dụng thông tin đã có để tổng hợp câu trả lời cho người dùng."
                    )
                }
                status = "duplicate_skipped"
            else:
                tool_result = self.tool_registry.execute_tool(tool_name, args, user)
                status = "success" if "error" not in tool_result else "error"

            record = ToolCallRecord(
                tool_name=tool_name,
                arguments=args if isinstance(args, dict) else {},
                execution_status=status,
                iteration_index=loop_state.iteration,
            )
            loop_state.executed_tools.append(record)
            events.append((tool_name, status, args if isinstance(args, dict) else {}))

            llm_messages.append({"role": "assistant", "content": None, "tool_calls": [tc]})
            llm_messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id", "call_default"),
                "name": tool_name,
                "content": json.dumps(tool_result, ensure_ascii=False),
            })
        return events

    async def _stream_llm_chunks(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        pending_tools: list[dict[str, Any]],
        state: dict[str, str],
    ) -> AsyncGenerator[str, None]:
        async for chunk in self.llm_client.stream_chat(messages, tools=tools):
            ctype, cdata = chunk.get("type"), chunk.get("data")
            if ctype == "reasoning":
                state["reasoning"] += str(cdata)
                yield f"data: {json.dumps({'type': 'reasoning', 'data': cdata}, ensure_ascii=False)}\n\n"
            elif ctype == "content":
                state["content"] += str(cdata)
                yield f"data: {json.dumps({'type': 'content', 'data': cdata}, ensure_ascii=False)}\n\n"
            elif ctype == "tool_calls_complete" and isinstance(cdata, list):
                pending_tools.extend(cdata)
            elif ctype == "error":
                yield f"data: {json.dumps({'type': 'error', 'data': cdata}, ensure_ascii=False)}\n\n"

    async def execute(
        self,
        message: str,
        session_id: UUID | None,
        user: AuthPrincipal,
    ) -> AsyncGenerator[str, None]:
        """Process chat message and yield SSE formatted chunks via an autonomous Agent Loop."""
        session, is_new = self._resolve_session(session_id, user.user_id, message)
        if is_new:
            payload = {"type": "session_created", "data": {"id": str(session.id), "title": session.title}}
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        self.repo.add_message(ChatMessage(session_id=session.id, role=MessageRole.USER, content=message))
        history = self.repo.get_session_messages(session.id, user.user_id)
        llm_messages = self._build_llm_messages(history[-8:])
        tools = self.tool_registry.get_tool_definitions(user)

        state = {"content": "", "reasoning": ""}
        loop_state = AgentLoopState(max_iterations=settings.CHATBOT_MAX_ITERATIONS)

        # Autonomous Agent Loop (ReAct / Multi-turn)
        while loop_state.iteration < loop_state.max_iterations:
            loop_state.iteration += 1
            yield f"data: {json.dumps({'type': 'iteration_step', 'data': {'iteration': loop_state.iteration, 'max_iterations': loop_state.max_iterations}}, ensure_ascii=False)}\n\n"

            # Check and prune context only when close to overflowing (~50k tokens threshold)
            self._prune_context_history_if_needed(llm_messages)

            pending_tools: list[dict[str, Any]] = []
            async for chunk in self._stream_llm_chunks(llm_messages, tools, pending_tools, state):
                yield chunk

            if not pending_tools:
                # LLM finished reasoning and returned final text
                loop_state.is_completed = True
                break

            # Execute tools and stream real-time tool trace events
            tool_events = self._execute_tools(pending_tools, user, llm_messages, loop_state)
            for t_name, t_status, _t_args in tool_events:
                yield f"data: {json.dumps({'type': 'tool_call_start', 'data': {'name': t_name, 'iteration': loop_state.iteration}}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'tool_call_end', 'data': {'name': t_name, 'status': t_status, 'iteration': loop_state.iteration}}, ensure_ascii=False)}\n\n"

        # Safeguard fallback if max_iterations reached without final text
        if not loop_state.is_completed and not state["content"]:
            llm_messages.append({
                "role": "user",
                "content": "Hãy tổng hợp lại toàn bộ thông tin tra cứu được ở trên để đưa ra câu trả lời chi tiết và kết luận cho người dùng.",
            })
            async for chunk in self._stream_llm_chunks(llm_messages, None, [], state):
                yield chunk

        meta = ChatMessageMetadata(
            model_name=self.llm_client.model,
            reasoning_content=state["reasoning"] or None,
            tools_invoked=loop_state.executed_tools,
        )
        self.repo.add_message(ChatMessage(session_id=session.id, role=MessageRole.ASSISTANT, content=state["content"], metadata_info=meta))
        yield f"data: {json.dumps({'type': 'done', 'data': state['content']}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
