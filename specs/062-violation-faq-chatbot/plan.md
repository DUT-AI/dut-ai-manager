# Implementation Plan: Chatbot Trợ Lý Giải Đáp Vi Phạm & Vận Hành Cho Thành Viên và Ban Quản Trị

**Branch**: `062-violation-faq-chatbot` | **Date**: 2026-11-12 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/062-violation-faq-chatbot/spec.md`

---

## Summary

Xây dựng hệ thống Chatbot Trợ lý ảo phục vụ 2 nhóm đối tượng:
1. **Thành viên (Member)**: Tự động tra cứu, giải đáp chi tiết nguyên nhân các vi phạm cá nhân (đi trễ, vắng họp, nộp bài muộn), hỏi đáp quy chế tổ chức, và được hướng dẫn liên hệ trực tiếp với bộ phận HR khi có thắc mắc.
2. **Ban Quản trị & Mentor (Admin/Mentor)**: Cung cấp trợ lý điều hành thông minh cho phép truy vấn nhanh số liệu vi phạm toàn hệ thống, danh sách thành viên vắng họp không phép, danh sách tồn đọng bài tập chưa nộp theo thời gian thực.

Hệ thống được thiết kế theo kiến trúc **Clean Architecture + Dishka DI**, giao thức truyền dữ liệu **Server-Sent Events (SSE) Streaming**, phân quyền công cụ thích ứng vai trò (**Role-Adaptive Tool Calling**) trên nền tảng **Private OpenAI-Compatible LLM (`https://llm2.dutai.site/v1`, model `ggml-org/gemma-4-e4b-it-GGUF:Q4_0`)**, lưu trữ tối đa **5 phiên hội thoại gần nhất** trên PostgreSQL, và giao diện kết hợp giữa trang riêng `/assistant` cùng nút biểu tượng nổi (Floating Action Icon) trên web.

---

## Technical Context

**Language/Version**: Python 3.12 (Backend), TypeScript 5.9 (Frontend)  
**Primary Dependencies**:
- Backend: FastAPI 0.128+, Dishka 1.9+, SQLAlchemy 2.0+ (asyncpg), Pydantic v2, OpenAI Async Client (`openai` hoặc `aiohttp`/`httpx`) kết nối `https://llm2.dutai.site/v1`.
- Frontend: React 19.2+, Vite 7.2+, TailwindCSS 4+, Ant Design 6.1+, `@tanstack/react-query`, `react-markdown`.

**Storage**: PostgreSQL (bảng `chat_sessions`, `chat_messages`), hỗ trợ cascade delete, indexes trên `user_id` và `created_at`.  
**Testing**: `pytest` (backend unit & integration), `vitest` / Playwright (frontend).  
**Target Platform**: Linux container (Docker Compose), Web Desktop & Mobile Browsers.  
**Project Type**: Fullstack Web Service (Web Frontend + FastAPI Backend REST/SSE).  
**Performance Goals**: Time-to-First-Token (TTFT) < 1.0 giây qua SSE streaming; truy vấn công cụ nội bộ < 150ms.  
**Constraints**:
- Không sử dụng Agent Harness tự trị phức tạp để tránh trễ và ảo giác.
- Bảo mật IDOR tuyệt đối: Thành viên không bao giờ truy cập được dữ liệu người khác.
- Giới hạn cứng tối đa 5 phiên chat cho mỗi người dùng (FIFO pruning).
- Lưu trữ timestamps chuẩn Timezone-Aware UTC theo Constitution.
- Sử dụng máy chủ LLM nội bộ `https://llm2.dutai.site/v1`, đảm bảo 100% dữ liệu không rò rỉ ra ngoài.

**Scale/Scope**: ~100-500 thành viên hoạt động, ~10.000 tin nhắn/tháng.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc Constitution | Trạng thái | Đánh giá tuân thủ trong Thiết kế |
| :--- | :---: | :--- |
| **I. Clean Architecture & Practical DDD** | ✅ PASS | Tách biệt triệt để: `domain/` (entities pure Pydantic), `application/` (single-responsibility use cases), `infrastructure/` (SQLAlchemy ORM, Gemini client, Tools registry), `presentation/` (`controller.py`, `schemas.py`). |
| **II. Dependency Injection with Dishka** | ✅ PASS | Đăng ký toàn bộ repository, use case, LLM service trong `providers.py` của domain `chatbot`, giải quyết bằng `@inject` và `FromDishka[...]`. |
| **III. Enterprise UTC Storage** | ✅ PASS | Toàn bộ `created_at`, `updated_at` trong `chat_sessions` và `chat_messages` sử dụng `DateTime(timezone=True)` và `datetime.now(UTC)`. |
| **IV. Event-Driven Decoupling** | ✅ PASS | Tách rời các tác vụ kiểm tra quyền và ghi log chat, không làm tắc nghẽn luồng xử lý chính. |
| **V. API Non-Null Contract DTOs** | ✅ PASS | Phản hồi danh sách phiên và tin nhắn sử dụng envelope chuẩn `ApiResponse[T]` với hợp đồng dữ liệu không null. |
| **VII. Single-Responsibility Use Cases** | ✅ PASS | Mỗi Use Case nằm trong file riêng (`send_chat_message_use_case.py`, `get_chat_sessions_use_case.py`, `delete_chat_session_use_case.py`, `get_quick_prompts_use_case.py`) với duy nhất 1 phương thức public `execute()`. |
| **VIII. Frontend Component Modularity** | ✅ PASS | Tách rời subcomponents (`ChatWindow`, `ChatMessageList`, `ChatMessageItem`, `ChatInput`, `ChatQuickPrompts`, `FloatingChatButton`) trong thư mục `components/`, page chỉ đóng vai trò orchestrator. |
| **XIII. Structured Generic Payload & Type Safety** | ✅ PASS | `metadata_json` được định nghĩa bằng `PydanticType(ChatMessageMetadata)` strongly-typed, nghiêm cấm `dict[str, Any]` thô. |
| **XIV. No Fake Optionals & Fail-Fast Contracts** | ✅ PASS | Các tham số bắt buộc trong constructor (`session_repo`, `llm_service`, `current_user`) được khai báo non-nullable tường minh. |

---

## Project Structure

### Documentation (this feature)

```text
specs/062-violation-faq-chatbot/
├── spec.md              # Đặc tả tính năng
├── plan.md              # Kế hoạch triển khai kỹ thuật (File này)
├── research.md          # Kết quả nghiên cứu & quyết định kiến trúc
├── data-model.md        # Thiết kế thực thể, ORM và quy tắc FIFO 5 phiên
├── quickstart.md        # Hướng dẫn xác thực và kiểm thử đầu cuối
├── contracts/
│   └── chat-api.yaml    # OpenAPI 3.1 Contract cho SSE Chat và Sessions
└── checklists/
    └── requirements.md  # Checklist kiểm định chất lượng đặc tả
```

### Source Code (repository root)

```text
backend/app/
└── chatbot/
    ├── __init__.py
    ├── controller.py                     # Router FastAPI (SSE streaming & Session REST)
    ├── schemas.py                        # Pydantic DTOs cho request/response
    ├── providers.py                      # Dishka Provider đăng ký DI
    ├── domain/
    │   ├── __init__.py
    │   ├── entity.py                     # ChatSession, ChatMessage, MessageRole
    │   └── value_objects.py              # ChatMessageMetadata, ToolCallRecord
    ├── application/
    │   ├── __init__.py
    │   ├── send_chat_message_use_case.py # Tiếp nhận message, gọi tool, stream SSE
    │   ├── get_chat_sessions_use_case.py # Lấy tối đa 5 phiên của user
    │   ├── get_session_messages_use_case.py # Lịch sử tin nhắn của 1 phiên
    │   ├── delete_chat_session_use_case.py  # Xóa phiên
    │   └── get_quick_prompts_use_case.py    # Gợi ý nhanh theo vai trò (Role-adaptive)
    └── infrastructure/
        ├── __init__.py
        ├── models.py                     # SQLAlchemy ChatSessionModel, ChatMessageModel
        ├── repository.py                 # ChatRepository (CRUD + FIFO 5 session pruning)
        ├── llm_client.py                 # Adapter giao tiếp OpenAI-compatible LLM (https://llm2.dutai.site/v1)
        ├── tools_registry.py             # Bộ công cụ gọi nội bộ (Personal + Admin tools)
        └── knowledge/
            └── violation_policies.md     # Nội quy và quy chế tổ chức chuẩn hóa

frontend/src/
└── features/
    └── chatbot/
        ├── index.ts                      # Public exports
        ├── pages/
        │   └── ChatbotPage.tsx           # Trang trợ lý đầy đủ (/assistant)
        ├── components/
        │   ├── index.ts
        │   ├── ai-elements/              # Các pattern chuẩn từ shadcn/ui AI Elements
        │   │   ├── Chat.tsx              # Container luồng chat & auto-scroll
        │   │   ├── Message.tsx           # Khung tin nhắn một lượt (User / Assistant)
        │   │   ├── PromptInput.tsx       # Ô nhập prompt mở rộng tự động + nút gửi
        │   │   ├── Reasoning.tsx         # Khung collapsible hiển thị suy nghĩ (reasoning_content từ Gemma)
        │   │   ├── Suggestion.tsx        # Chip câu hỏi gợi ý nhanh (Quick Prompts)
        │   │   └── ToolTrace.tsx         # Hiển thị trạng thái gọi tool (Đang tra cứu vi phạm...)
        │   ├── ChatSessionSidebar.tsx    # Danh sách 5 phiên bên trái (trên ChatbotPage)
        │   └── FloatingChatButton.tsx    # Nút tròn nổi góc phải màn hình + Popover
        ├── hooks/
        │   ├── useChatbot.ts             # Hook quản lý gửi tin nhắn, SSE streaming
        │   └── useChatSessions.ts        # Hook react-query quản lý danh sách phiên
        ├── services/
        │   └── chatbot.service.ts        # Axios & Fetch streaming client
        └── types/
            └── chatbot.types.ts          # TypeScript interfaces ánh xạ từ OpenAPI
```

---

## Complexity Tracking

> **Constitution Check: Không có vi phạm kiến trúc nào cần bào chữa (100% PASS).**

| Thiết kế | Lý do Lựa chọn | Giải pháp Đơn giản hơn bị Bác bỏ vì |
| :--- | :--- | :--- |
| **Native Function Calling thay vì Agent Harness** | Tốc độ nhanh (<1s), chính xác, không ảo giác số liệu vi phạm cá nhân | Agent Harness quá phức tạp, độ trễ cao (>10s), tốn token và tiềm ẩn nguy cơ vòng lặp vô tận |
| **Server-Sent Events (SSE) thay vì WebSocket** | Nhẹ nhàng, chuẩn HTTP, dễ phân quyền JWT, tương thích tốt với Reverse Proxy | WebSocket yêu cầu quản lý trạng thái kết nối socket hai chiều phức tạp không cần thiết cho luồng hỏi-đáp |
| **FIFO 5 Phiên lưu trữ Database** | Người dùng xem lại được ngữ cảnh trên mọi thiết bị; cố định dung lượng lưu trữ | Lưu LocalStorage không đồng bộ; lưu không giới hạn gây phình to database |
