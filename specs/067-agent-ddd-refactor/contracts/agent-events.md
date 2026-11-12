# Interface Contracts: Agent Events & SSE Output

**Feature Branch**: `067-agent-ddd-refactor`
**Date**: 2026-11-12

---

## 1. Domain Event Contract: `AgentStreamEvent`

Tầng Domain (`Agent`) giao tiếp với tầng Application (`SendChatMessageUseCase`) qua luồng bất đồng bộ sinh ra các đối tượng `AgentStreamEvent`:

| `event_type` | Cấu trúc `data` | Ý nghĩa |
| :--- | :--- | :--- |
| `iteration_step` | `{"iteration": int, "max_iterations": int}` | Bắt đầu một vòng lặp suy luận ReAct |
| `reasoning` | `str` (chuỗi token suy luận) | Delta nội dung suy luận của mô hình tư duy |
| `content` | `str` (chuỗi token văn bản) | Delta nội dung văn bản câu trả lời |
| `tool_call_start` | `{"name": str, "iteration": int}` | Bắt đầu thực thi một công cụ |
| `tool_call_end` | `{"name": str, "status": "success" \| "error" \| "duplicate_skipped", "iteration": int}` | Kết thúc thực thi công cụ |
| `error` | `str` (thông báo lỗi) | Có lỗi xảy ra trong quá trình gọi LLM |
| `complete` | `{"content": str, "metadata": ChatMessageMetadata}` | Hoàn tất chu trình Agent, trả về toàn bộ kết quả |

---

## 2. Server-Sent Events (SSE) Contract (Frontend API)

Tầng Application (`SendChatMessageUseCase`) ánh xạ trực tiếp từ `AgentStreamEvent` sang định dạng chuẩn SSE gửi về client qua HTTP endpoint `POST /api/chatbot/sessions/send-stream`:

```text
data: {"type": "session_created", "data": {"id": "01931ebc-...", "title": "Kiểm tra vi phạm"}}

data: {"type": "iteration_step", "data": {"iteration": 1, "max_iterations": 5}}

data: {"type": "reasoning", "data": "Đang phân tích bảng vi phạm..."}

data: {"type": "tool_call_start", "data": {"name": "db_execute_query", "iteration": 1}}

data: {"type": "tool_call_end", "data": {"name": "db_execute_query", "status": "success", "iteration": 1}}

data: {"type": "content", "data": "Chào bạn, bạn hiện không có vi phạm nào."}

data: {"type": "done", "data": "Chào bạn, bạn hiện không có vi phạm nào."}

data: [DONE]
```

Contract này hoàn toàn tương thích ngược 100% với giao diện người dùng React (`src/features/chatbot/pages/ChatbotPage.tsx`).
