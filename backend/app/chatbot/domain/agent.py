"""Domain Service Agent orchestrating reasoning, tool calling, and context management."""

import json
from collections.abc import AsyncGenerator
from typing import Any

from app.chatbot.domain.entity import ChatMessage
from app.chatbot.domain.value_objects import (
    AgentLoopState,
    AgentStreamEvent,
    ChatMessageMetadata,
    ToolCallRecord,
)
from app.chatbot.infrastructure.llm_client import LLMClient
from app.chatbot.infrastructure.tools_registry import ChatbotToolRegistry
from app.core.config import settings
from app.core.principal import AuthPrincipal

DUT_ASSISTANT_SYSTEM_PROMPT = """
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


class Agent:
    """Domain Service executing autonomous ReAct reasoning loop, tool calling, and context pruning."""

    def __init__(
        self,
        llm_client: LLMClient,
        tool_registry: ChatbotToolRegistry,
        max_iterations: int = settings.CHATBOT_MAX_ITERATIONS,
        prune_token_threshold: int = settings.CHATBOT_PRUNE_TOKEN_THRESHOLD,
    ) -> None:
        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self.max_iterations = max_iterations
        self.prune_token_threshold = prune_token_threshold

    def build_llm_messages(
        self, recent_history: list[ChatMessage]
    ) -> list[dict[str, Any]]:
        """Construct the initial messages list with system instructions and recent conversation."""
        llm_messages: list[dict[str, Any]] = [
            {"role": "system", "content": DUT_ASSISTANT_SYSTEM_PROMPT}
        ]
        for msg in recent_history:
            llm_messages.append({"role": msg.role.value, "content": msg.content})
        return llm_messages


    async def prune_context_if_needed(
        self,
        llm_messages: list[dict[str, Any]],
        max_threshold: int | None = None,
    ) -> None:
        """Prunes historical tool results when total context exceeds the safe threshold."""
        threshold = max_threshold if max_threshold is not None else self.prune_token_threshold
        current_tokens = await self.llm_client.count_tokens(llm_messages)
        if current_tokens < threshold:
            return

        for msg in llm_messages:
            if msg.get("role") == "tool" and len(str(msg.get("content") or "")) > 300:
                raw_content = str(msg.get("content") or "")
                msg["content"] = raw_content[:250] + "... [Dữ liệu đã được tóm tắt để tối ưu bộ nhớ context]"
                if await self.llm_client.count_tokens(llm_messages) < threshold:
                    break

    def _execute_tools(
        self,
        pending_tool_calls: list[dict[str, Any]],
        user: AuthPrincipal,
        llm_messages: list[dict[str, Any]],
        loop_state: AgentLoopState,
    ) -> list[tuple[str, str, dict[str, Any]]]:
        """Executes pending tools with infinite loop prevention and records them into loop_state.

        Returns list of (tool_name, status, args) for trace events.
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

            # Detect duplicate tool calls in the same loop
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
        state: dict[str, Any],
    ) -> AsyncGenerator[AgentStreamEvent, None]:
        """Stream chunks from LLM client and yield strongly-typed AgentStreamEvents."""
        async for chunk in self.llm_client.stream_chat(messages, tools=tools):
            ctype, cdata = chunk.get("type"), chunk.get("data")
            if ctype == "reasoning":
                state["reasoning"] += str(cdata)
                yield AgentStreamEvent(event_type="reasoning", data=cdata)
            elif ctype == "content":
                state["content"] += str(cdata)
                yield AgentStreamEvent(event_type="content", data=cdata)
            elif ctype == "usage" and isinstance(cdata, dict):
                state["usage"] = cdata.get("usage")
                state["timings"] = cdata.get("timings")
                yield AgentStreamEvent(event_type="usage", data=cdata)
            elif ctype == "tool_calls_complete" and isinstance(cdata, list):
                pending_tools.extend(cdata)
            elif ctype == "error":
                yield AgentStreamEvent(event_type="error", data=cdata)

    async def run_stream(
        self,
        recent_history: list[ChatMessage],
        user: AuthPrincipal,
    ) -> AsyncGenerator[AgentStreamEvent, None]:
        """Executes autonomous multi-turn ReAct reasoning loop, yielding AgentStreamEvents."""
        llm_messages = self.build_llm_messages(recent_history)
        tools = self.tool_registry.get_tool_definitions(user)

        state: dict[str, Any] = {
            "content": "",
            "reasoning": "",
            "usage": None,
            "timings": None,
        }
        loop_state = AgentLoopState(max_iterations=self.max_iterations)

        while loop_state.iteration < loop_state.max_iterations:
            loop_state.iteration += 1
            yield AgentStreamEvent(
                event_type="iteration_step",
                data={"iteration": loop_state.iteration, "max_iterations": loop_state.max_iterations},
            )

            await self.prune_context_if_needed(llm_messages)

            pending_tools: list[dict[str, Any]] = []
            async for event in self._stream_llm_chunks(llm_messages, tools, pending_tools, state):
                yield event

            if not pending_tools:
                loop_state.is_completed = True
                break

            tool_events = self._execute_tools(pending_tools, user, llm_messages, loop_state)
            for t_name, t_status, _t_args in tool_events:
                yield AgentStreamEvent(
                    event_type="tool_call_start",
                    data={"name": t_name, "iteration": loop_state.iteration},
                )
                yield AgentStreamEvent(
                    event_type="tool_call_end",
                    data={"name": t_name, "status": t_status, "iteration": loop_state.iteration},
                )

        if not loop_state.is_completed and not state["content"]:
            llm_messages.append({
                "role": "user",
                "content": "Hãy tổng hợp lại toàn bộ thông tin tra cứu được ở trên để đưa ra câu trả lời chi tiết và kết luận cho người dùng.",
            })
            async for event in self._stream_llm_chunks(llm_messages, None, [], state):
                yield event

        metadata = ChatMessageMetadata(
            model_name=self.llm_client.model,
            reasoning_content=state["reasoning"] or None,
            tools_invoked=loop_state.executed_tools,
            usage=state.get("usage"),
            timings=state.get("timings"),
        )
        yield AgentStreamEvent(
            event_type="complete",
            data={"content": state["content"], "metadata": metadata},
        )
