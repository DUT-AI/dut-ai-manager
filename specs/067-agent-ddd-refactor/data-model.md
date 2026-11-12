# Data Model & Domain Design: Chatbot Agent DDD Refactor

**Feature Branch**: `067-agent-ddd-refactor`
**Date**: 2026-11-12

---

## 1. Domain Entities & Aggregate Roots

### `ChatSession` (Aggregate Root)
Quản lý phiên hội thoại và danh sách tin nhắn của người dùng (tối đa 5 phiên hoạt động):
- `id: UUID`: Khóa chính định danh phiên (UUIDv7).
- `user_id: int`: Mã người dùng sở hữu.
- `title: str`: Tiêu đề tóm tắt phiên trò chuyện.
- `created_at: datetime`: Thời điểm tạo phiên (UTC).
- `updated_at: datetime`: Thời điểm cập nhật cuối (UTC).
- Phương thức nghiệp vụ:
  - `update_title_from_first_message(first_message: str) -> None`: Tự động cắt gọt 50 ký tự đầu làm tiêu đề phiên.

### `ChatMessage` (Domain Entity)
Đại diện cho một tin nhắn trong phiên:
- `id: UUID`: Khóa chính định danh tin nhắn (UUIDv7).
- `session_id: UUID`: Liên kết tới `ChatSession`.
- `role: MessageRole`: Vai trò người gửi (`USER`, `ASSISTANT`, `SYSTEM`).
- `content: str`: Nội dung văn bản của tin nhắn.
- `metadata_info: ChatMessageMetadata`: Siêu dữ liệu strongly-typed.
- `created_at: datetime`: Thời điểm gửi (UTC).

---

## 2. Value Objects & Domain Models

### `AgentStreamEvent` (Domain Value Object)
Mô hình hóa các sự kiện phát ra từ chu trình reasoning của `Agent`:
```python
class AgentStreamEvent(BaseModel):
    event_type: str  # "iteration_step" | "tool_call_start" | "tool_call_end" | "reasoning" | "content" | "usage" | "error" | "complete"
    data: Any
```
- Khi `event_type == "complete"`, `data` là dictionary chứa `content: str` và `metadata: ChatMessageMetadata`.

### `AgentLoopState` (Domain Value Object)
Trạng thái của chu trình Agent Loop:
- `iteration: int`: Vòng lặp hiện tại (bắt đầu từ 0).
- `max_iterations: int`: Số vòng lặp tối đa cho phép (mặc định 5).
- `accumulated_content: str`: Văn bản tích lũy từ LLM.
- `accumulated_reasoning: str`: Nội dung suy luận tích lũy.
- `executed_tools: list[ToolCallRecord]`: Danh sách các công cụ đã thực thi.
- `call_signatures: set[str]`: Tập hợp các chữ ký `f"{tool_name}:{args}"` chống gọi lặp.
- `is_completed: bool`: Đánh dấu chu trình đã hoàn tất thành công.
- Phương thức:
  - `add_call_signature(tool_name: str, args: dict[str, Any]) -> bool`

### `ChatMessageMetadata` (Domain Value Object)
- `model_name: str`: Tên model LLM phục vụ.
- `reasoning_content: str | None`: Nội dung suy luận tư duy của mô hình.
- `tools_invoked: list[ToolCallRecord]`: Danh sách công cụ đã gọi.
- `citations: list[str]`: Nguồn tham chiếu/trích dẫn nếu có.
- `usage: dict[str, Any] | None`: Thống kê token (`prompt_tokens`, `completion_tokens`, `total_tokens`...).
- `timings: dict[str, Any] | None`: Thống kê tốc độ xử lý của server inference.

---

## 3. Domain Services & Application Use Case

### `Agent` (Domain Service)
Tọa lạc tại `backend/app/chatbot/domain/agent.py`:
- Thuộc tính phụ thuộc:
  - `llm_client: LLMClient`: Adapter giao tiếp mạng với máy chủ LLM.
  - `tool_registry: ChatbotToolRegistry`: Registry phân giải và thực thi các công cụ có kiểm soát quyền hạn.
  - `max_iterations: int`: Giới hạn lặp tối đa.
  - `prune_token_threshold: int`: Ngưỡng token để kích hoạt cắt tỉa context.
- Phương thức chính:
  - `async def run_stream(self, recent_history: list[ChatMessage], user: AuthPrincipal) -> AsyncGenerator[AgentStreamEvent, None]`: Chạy toàn bộ chu trình ReAct Agent và yield các `AgentStreamEvent`.
  - `async def _prune_context_if_needed(self, messages: list[dict[str, Any]]) -> None`: Nén dữ liệu công cụ cũ khi vượt ngưỡng an toàn.
  - `_build_messages(self, recent_history: list[ChatMessage]) -> list[dict[str, Any]]`: Khởi tạo danh sách message kèm system prompt.

### `SendChatMessageUseCase` (Application Layer Orchestrator)
Tọa lạc tại `backend/app/chatbot/application/send_chat_message_use_case.py`:
- Thuộc tính phụ thuộc:
  - `repo: ChatRepository`: Quản lý truy xuất và lưu trữ phiên, tin nhắn.
  - `agent: Agent`: Domain service thực thi chu trình suy luận của Agent.
- Phương thức duy nhất:
  - `async def execute(self, message: str, session_id: UUID | None, user: AuthPrincipal) -> AsyncGenerator[str, None]`:
    1. Xác định phiên (`_resolve_session`).
    2. Lưu tin nhắn User vào database.
    3. Lấy 8 tin nhắn gần nhất từ DB.
    4. Gọi `self.agent.run_stream(recent_history, user)`.
    5. Định dạng mỗi event thành SSE string `data: { ... }\n\n` và yield về.
    6. Khi nhận event `complete`: Lưu tin nhắn Assistant vào DB với metadata.
    7. Yield `data: [DONE]\n\n`.
