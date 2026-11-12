# Research & Architectural Decisions: Chatbot Agent DDD Refactor

**Feature Branch**: `067-agent-ddd-refactor`
**Date**: 2026-11-12

---

## 1. Domain Service: Agent Architecture & Responsibilities

### Problem
Hiện tại, `SendChatMessageUseCase` dài hơn 245 dòng mã, gánh vác quá nhiều trách nhiệm:
- Lưu trữ và định dạng System Prompt (`SYSTEM_PROMPT`).
- Quản lý token estimation và thuật toán cắt tỉa ngữ cảnh (`_prune_context_history_if_needed`).
- Xử lý chi tiết các SSE chunk từ `LLMClient` (`_stream_llm_chunks`).
- Điều phối vòng lặp ReAct (`AgentLoopState`, tối đa `max_iterations`, fallback prompt khi cạn vòng lặp).
- Kiểm tra chữ ký gọi công cụ chống trùng lặp (`loop_state.add_call_signature`).
- Định dạng tin nhắn gửi sang LLM và tin nhắn kết quả của tool (`role: "tool"`).

Use Case vi phạm Nguyên tắc I (Clean Architecture), Nguyên tắc VII (Single Responsibility Use Case) và Nguyên tắc IX (Pure Composition & Domain Services) của Constitution dự án.

### Decision
Tách toàn bộ logic suy luận và chu trình vòng lặp công cụ ra thành một Domain Service có tên là **`Agent`** đặt tại `backend/app/chatbot/domain/agent.py`.

- **Trách nhiệm của `Agent`**:
  1. Chuẩn bị ngữ cảnh hội thoại cho LLM (`build_messages`), kết hợp với `DUT_ASSISTANT_SYSTEM_PROMPT`.
  2. Áp dụng chính sách cắt tỉa ngữ cảnh (`prune_context_if_needed`) khi token vượt ngưỡng quy định.
  3. Quản lý vòng lặp ReAct / Multi-turn Tool Chaining:
     - Gửi yêu cầu đến `LLMClient`.
     - Phân tích cú pháp delta/chunk (reasoning, content, tool_calls, usage, timings).
     - Kiểm tra và thực thi công cụ qua `ChatbotToolRegistry` (chống trùng lặp qua chữ ký signature).
     - Đưa kết quả công cụ vào ngữ cảnh và lặp lại cho đến khi mô hình hoàn thành hoặc đạt giới hạn vòng lặp.
     - Kích hoạt fallback prompt nếu chạm ngưỡng lặp mà chưa có phản hồi văn bản cuối cùng.
  4. Trả về luồng các sự kiện miền (`AgentStreamEvent`) chứa tiến trình suy luận và đối tượng `ChatMessageMetadata` hoàn chỉnh.

- **Trách nhiệm của `SendChatMessageUseCase`**:
  1. Chỉ đóng vai trò **Orchestrator** điều phối luồng:
     - Tiếp nhận tham số (`message`, `session_id`, `user`).
     - Giải quyết phiên trò chuyện (`_resolve_session`).
     - Lưu tin nhắn của người dùng (`ChatMessage` role `USER`).
     - Lấy lịch sử tin nhắn gần nhất từ `ChatRepository`.
     - Khởi chạy `agent.run_stream(...)`.
     - Chuyển tiếp các sự kiện của Agent thành định dạng SSE tương thích 100% với Frontend.
     - Khi nhận được kết quả hoàn tất (`AgentCompletionEvent`), lưu tin nhắn `ChatMessage` role `ASSISTANT` vào cơ sở dữ liệu.

---

## 2. Event Model giữa Agent và Use Case

### Decision
Sử dụng mô hình sự kiện miền nhẹ (Value Object / Pydantic Dataclass) để truyền tải thông điệp giữa `Agent` và `SendChatMessageUseCase`:

```python
class AgentStreamEvent(BaseModel):
    event_type: str  # "iteration_step" | "tool_call_start" | "tool_call_end" | "reasoning" | "content" | "usage" | "error" | "complete"
    data: Any
```

Khi Agent chạy xong chu trình, nó phát ra event loại `complete` chứa:
- `content: str`: Văn bản trả lời cuối cùng.
- `metadata: ChatMessageMetadata`: Bao gồm `model_name`, `reasoning_content`, `tools_invoked`, `usage`, `timings`.

Nhờ vậy, `SendChatMessageUseCase` không cần biết chi tiết bên trong chu trình suy luận mà chỉ cần chuyển tiếp (map) event tương ứng sang SSE stream `data: { ... }\n\n` cho client.

---

## 3. Dependency Injection với Dishka

### Decision
Cập nhật `backend/app/chatbot/providers.py`:
- Khai báo dependency provider cho `Agent`:
  ```python
  @provide(scope=Scope.REQUEST)
  def provide_chatbot_agent(
      self,
      llm_client: LLMClient,
      tool_registry: ChatbotToolRegistry,
  ) -> Agent:
      return Agent(
          llm_client=llm_client,
          tool_registry=tool_registry,
          max_iterations=settings.CHATBOT_MAX_ITERATIONS,
          prune_token_threshold=settings.CHATBOT_PRUNE_TOKEN_THRESHOLD,
      )
  ```
- Cập nhật provider cho `SendChatMessageUseCase`:
  ```python
  @provide(scope=Scope.REQUEST)
  def provide_send_chat_message_use_case(
      self,
      repo: ChatRepository,
      agent: Agent,
  ) -> SendChatMessageUseCase:
      return SendChatMessageUseCase(repo=repo, agent=agent)
  ```

---

## 4. Tương thích ngược và Zero Regression

- Hợp đồng SSE với frontend (`data: {"type": ..., "data": ...}\n\n`) giữ nguyên 100%.
- Cơ sở dữ liệu và các Entity (`ChatSession`, `ChatMessage`, `ChatMessageMetadata`) không thay đổi cấu trúc bảng.
- Cập nhật các bài unit test trong `tests/unit/test_chatbot.py` để tương thích với cấu trúc injection mới (`Agent`), đồng thời bổ sung unit test độc lập cho `Agent`.
