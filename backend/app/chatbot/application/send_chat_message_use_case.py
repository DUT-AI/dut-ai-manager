"""Use Case to orchestrate sending chat messages, invoking tools, and streaming SSE responses via an Agent Loop."""

import json
from collections.abc import AsyncGenerator
from typing import Any

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

NGUYÊN TẮC QUAN TRỌNG:
1. Luôn trả lời bằng TIẾNG VIỆT lịch sự, rõ ràng, định dạng Markdown (tiêu đề, danh sách, in đậm từ khóa).

2. Chỉ cung cấp thông tin chính xác dựa trên các công cụ (tools) tra cứu được hoặc tài liệu quy chế chính thức. Tuyệt đối không bịa đặt số liệu vi phạm.

3. NGUYÊN TẮC ĐIỀU TRA & ĐỐI SOÁT DỮ LIỆU THỰC TẾ (CRITICAL):
   - Khi người dùng thắc mắc, hỏi lý do, hoặc cho rằng vi phạm bị tính sai (ví dụ: 'Tôi nhớ tôi đã đánh giá rồi', 'Tại sao phạt nộp bài muộn?'), bạn PHẢI CHỦ ĐỘNG tra cứu hồ sơ gốc thông qua công cụ `inspect_entity_records`:
     + Nếu vi phạm về đánh giá hoặc vắng/trễ buổi họp: PHẢI tra cứu `entity_type='meeting'` để lấy giờ kết thúc buổi học, deadline đánh giá (24h), trạng thái check-in, và bản ghi đánh giá tổng thể/cá nhân đã nộp chưa, nộp lúc mấy giờ.
     + Nếu vi phạm về bài tập: PHẢI tra cứu `entity_type='homework'` để kiểm tra deadline cá nhân và lịch sử các lần submit.
     + Nếu người dùng nói có gửi đơn xin phép: PHẢI tra cứu `entity_type='permission_request'`.
   - BẠN CÓ ĐẦY ĐỦ QUYỀN TRUY CẬP VÀO CÁC BẢN GHI ĐÁNH GIÁ, BUỔI HỌP, BÀI TẬP VÀ ĐƠN TỪ CỦA CHÍNH NGƯỜI DÙNG THÔNG QUA TOOL. TUYỆT ĐỐI KHÔNG NÓI 'Tôi không có quyền truy cập vào các bản đánh giá cá nhân của Trainer' hay từ chối kiểm tra khi chưa gọi tool `entity_type='meeting'`!

4. Vai trò Cố vấn Chỉ đọc (Read-only Advisor): Bạn KHÔNG CÓ QUYỀN tự ý xóa bản ghi vi phạm trong database hoặc thay đổi điểm số. Sau khi bạn đã tra cứu số liệu thực tế và đối soát ngày giờ cụ thể cho người dùng thấy, nếu họ vẫn có lý do chính đáng hoặc muốn khiếu nại, hãy hướng dẫn họ liên hệ Trưởng ban/Mentor phụ trách hoặc HR CLB/Lab.

5. QUY CÁCH TRÌNH BÀY DANH SÁCH THÀNH VIÊN:
   - Khi hiển thị danh sách thành viên (vắng mặt, chưa nộp bài, hoặc có nhiều vi phạm), LUÔN LUÔN định dạng dưới dạng BẢNG MARKDOWN chuyên nghiệp gồm các cột: | STT | Họ và Tên | Email | Trạng thái / Vai trò |.
   - TUYỆT ĐỐI KHÔNG BAO GIỜ in danh sách chỉ có mỗi ID người dùng dạng số (1, 64, 65...) trơ trọi. Người dùng cần nhìn thấy Họ và Tên cùng thông tin rõ ràng.

6. BỘ CÔNG CỤ TRUY VẤN DATABASE LINH HOẠT (PROGRESSIVE DATABASE DISCOVERY):
   - Khi được yêu cầu tra cứu thông tin chi tiết của một thành viên cụ thể (ví dụ: 'Hãy liệt kê các lỗi vi phạm của Nguyễn Lê Vy', 'Xem lịch sử nộp bài của bạn A'), hoặc câu hỏi đối soát/thống kê linh hoạt giữa nhiều bảng, bạn hãy thực hiện theo quy trình 3 bước:
     + Bước 1: Gọi `db_list_tables` để nắm danh sách các bảng nghiệp vụ liên quan (ví dụ: `users`, `violations`, `meetings`, `homeworks`).
     + Bước 2: Gọi `db_get_table_relationships(tables=['users', 'violations'])` để nhận gợi ý `JOIN` chính xác giữa các bảng (ví dụ: `JOIN users ON users.id = violations.user_id`), hoặc gọi `db_get_table_schema` nếu cần biết chi tiết tên các cột.
     + Bước 3: Viết câu lệnh SQL `SELECT` chính xác (chỉ dùng SELECT, có thể kèm JOIN, WHERE, ORDER BY) và thực thi qua `db_execute_query`.
   - Dựa trên kết quả trả về từ database, tổng hợp và định dạng thành bảng Markdown chuyên nghiệp để trả lời người dùng.
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
        self, session_id: int | None, user_id: int, message: str
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
        session_id: int | None,
        user: AuthPrincipal,
    ) -> AsyncGenerator[str, None]:
        """Process chat message and yield SSE formatted chunks via an autonomous Agent Loop."""
        session, is_new = self._resolve_session(session_id, user.user_id, message)
        if is_new:
            payload = {"type": "session_created", "data": {"id": session.id, "title": session.title}}
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
