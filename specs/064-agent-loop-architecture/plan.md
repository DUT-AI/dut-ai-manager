# Implementation Plan: Nâng cấp kiến trúc chatbot thành Agent Loop (ReAct / Multi-turn Tool Loop)

**Feature ID**: `064-agent-loop-architecture`  
**Branch**: `064-agent-loop-architecture`  
**Trạng thái**: In Planning  

---

## Technical Context

- **Backend**: FastAPI, Python 3.12, SQLAlchemy 2.0, Dishka DI.
- **Chatbot Module**: `backend/app/chatbot/`
  - Core Use Case: `SendChatMessageUseCase` (`application/send_chat_message_use_case.py`).
  - LLM Client: `LLMClient` (`infrastructure/llm_client.py`).
  - Tool Registry: `ChatbotToolRegistry` (`infrastructure/tools_registry.py`).
- **Testing**: `backend/tests/unit/test_chatbot.py` (Pytest).
- **Frontend**: React 19, Vite, Tailwind CSS v4, shadcn/ui AI Elements (`frontend/src/features/chatbot/`).

---

## Constitution Check

- [x] **I. Clean Architecture & DDD**: Tách biệt logic vòng lặp trong Application layer (`AgentLoopOrchestrator` hoặc nâng cấp `SendChatMessageUseCase`), không đưa business logic vào Controller hay Presentation.
- [x] **II. Dependency Injection with Dishka**: `LLMClient`, `ChatRepository`, và `ChatbotToolRegistry` được inject qua Dishka providers (`app/chatbot/providers.py`).
- [x] **III. Enterprise UTC**: Mọi timestamp ghi log hay metadata đều dùng timezone-aware UTC.
- [x] **VII. Strict Single-Responsibility Use Cases**: `SendChatMessageUseCase` giữ nguyên trách nhiệm duy nhất là xử lý yêu cầu gửi tin nhắn và stream SSE.
- [x] **VIII. Frontend Component Modularity**: Giữ nguyên tính độc lập của các subcomponents trong `frontend/src/features/chatbot/components/ai-elements/`.
- [x] **X. Zero Redundant Backward Compatibility**: Tối ưu trực tiếp giao thức streaming, không tạo wrapper rườm rà.

---

## Phases & Milestones

### Phase 0: Research & Architecture Design (Hoàn tất)
- [x] Nghiên cứu 4 mô hình Agent Loop (ReAct, Plan-and-Execute, LangGraph, Multi-Agent).
- [x] Lựa chọn mô hình **Enhanced ReAct Loop** phù hợp với model 4B on-premise.
- [x] Tài liệu hóa `specs/064-agent-loop-architecture/research.md` và `data-model.md`.

### Phase 1: Core Agent Loop Engine (Backend)
- [ ] Xây dựng `AgentLoopRunner` hoặc refactor `SendChatMessageUseCase` để triển khai vòng lặp `while iteration < max_iterations`:
  - Lượt 1: LLM stream suy luận -> Nếu có tool calls:
    - Kiểm tra phát hiện trùng lặp (`call_signatures`).
    - Thực thi tool qua `ChatbotToolRegistry`.
    - Yield SSE event thông báo tool bắt đầu / kết thúc.
    - Đính kèm kết quả tool vào ngữ cảnh hội thoại.
    - Tiếp tục vòng lặp kế tiếp với `tools=available_tools`.
  - Dừng vòng lặp khi: LLM không gọi thêm tool nào (trả về content thuần) HOẶC đạt `max_iterations = 5`.
- [ ] Thêm cơ chế **Context Pruning khi chạm ngưỡng trần**: Vì cửa sổ ngữ cảnh thực tế của model lên tới **66,816 tokens**, cơ chế Pruning chỉ kích hoạt khi ước tính tổng context vượt ngưỡng an toàn (~50,000 tokens), bảo tồn tối đa dữ liệu chi tiết của các tool.
- [ ] Bổ sung bảo vệ Timeout và ngắt lặp vô tận (Loop Breaker).

### Phase 2: Unit Testing & Verification
- [ ] Viết unit tests kiểm thử chuỗi tool liên hoàn (Multi-step tool chaining: Tool A -> Tool B -> Final Answer).
- [ ] Viết unit test kiểm thử cơ chế chặn lặp vô tận khi LLM lặp lại cùng một tool call.
- [ ] Viết unit test kiểm thử chạm ngưỡng `max_iterations`.

### Phase 3: Frontend Integration & Real-time Tool Trace Sync
- [ ] Cập nhật `chatbot.service.ts` để nhận các event SSE mới (`tool_call_start`, `tool_call_end`, `iteration_step`).
- [ ] Hiển thị trực quan trạng thái từng bước chạy trong component `MessageItem` / `ToolTrace` của shadcn AI Elements.
- [ ] Kiểm thử E2E trực tiếp trên trình duyệt.
