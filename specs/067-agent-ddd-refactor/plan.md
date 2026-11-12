# Implementation Plan: Chatbot Agent DDD Refactor

**Branch**: `067-agent-ddd-refactor` | **Date**: 2026-11-12 | **Spec**: [specs/067-agent-ddd-refactor/spec.md](spec.md)

**Input**: Feature specification from `specs/067-agent-ddd-refactor/spec.md`

## Summary

Tái cấu trúc kiến trúc của mô-đun Chatbot theo chuẩn Domain-Driven Design (DDD) & Clean Architecture:
- Chuyển `SendChatMessageUseCase` thành một Single-Responsibility Orchestrator mỏng (< 120 dòng), chỉ lo điều phối phiên hội thoại, lưu tin nhắn vào cơ sở dữ liệu qua `ChatRepository`, kích hoạt luồng xử lý và phát luồng SSE về Presentation.
- Tạo Domain Service **`Agent`** (`backend/app/chatbot/domain/agent.py`) để đóng gói toàn bộ logic nghiệp vụ cốt lõi: vòng lặp ReAct / Multi-turn Tool Chaining, System Prompt chỉ thị, phát hiện trùng lặp công cụ (`loop_state.add_call_signature`), chính sách cắt tỉa ngữ cảnh (`ContextPruningPolicy`), và đóng gói siêu dữ liệu hoàn chỉnh (`ChatMessageMetadata`).
- Sử dụng mô hình sự kiện miền `AgentStreamEvent` để giao tiếp giữa Domain Service và Use Case.
- Cập nhật cấu hình Dishka Dependency Injection (`backend/app/chatbot/providers.py`).

## Technical Context

**Language/Version**: Python 3.12 (Backend)

**Primary Dependencies**: FastAPI, Dishka (Dependency Injection), Pydantic v2, SQLAlchemy 2.0, aiohttp

**Storage**: PostgreSQL (`chat_sessions`, `chat_messages` với UUIDv7 Primary Keys)

**Testing**: pytest, pytest-asyncio

**Target Platform**: Linux / macOS Docker environments

**Project Type**: Web API Service (Clean Architecture / Domain-Driven Design)

**Performance Goals**: Không tăng thêm độ trễ streaming, nén context hiệu quả khi vượt ngưỡng 50k token, bảo toàn thời gian phản hồi theo thời gian thực.

**Constraints**:
- Giữ vững 100% hợp đồng SSE giao tiếp với Frontend React (`ChatbotPage.tsx`).
- Tuân thủ nghiêm ngặt Constitution: Nguyên tắc I (Clean Architecture), Nguyên tắc II (Dishka DI), Nguyên tắc VII (Single Responsibility Use Case), Nguyên tắc IX (Pure Composition Over Base Use Cases), Nguyên tắc XIV (Fail-Fast Parameter Contracts).
- Giữ 100% pass rate cho 16 unit tests hiện tại.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc Constitution | Đánh giá | Ghi chú thiết kế |
| :--- | :---: | :--- |
| **I. Clean Architecture & Practical DDD** | **PASS** | Tách biệt rạch ròi: Domain Service `Agent` chứa pure reasoning/tool orchestration logic; Use Case `SendChatMessageUseCase` chỉ là Orchestrator mỏng; Repository lo lưu trữ DB. |
| **II. Dependency Injection with Dishka** | **PASS** | `Agent` được đăng ký trong `backend/app/chatbot/providers.py` và inject trực tiếp vào `SendChatMessageUseCase` qua constructor injection. |
| **VII. Strict Single-Responsibility Use Cases** | **PASS** | `SendChatMessageUseCase` có 1 method `execute` duy nhất, không ôm đồm prompt, token estimation, hay vòng lặp tool execution. |
| **IX. Pure Composition & Domain Services** | **PASS** | Dùng Domain Service `Agent` qua thành phần cấu thành (composition), không sử dụng thừa kế hay abstract base use case. |
| **XIV. No Fake Optionals & Fail-Fast Contracts** | **PASS** | Các tham số khởi tạo `Agent` (`llm_client`, `tool_registry`, `max_iterations`, `prune_threshold`) đều là non-nullable mandatory parameters. |

## Project Structure

### Documentation (this feature)

```text
specs/067-agent-ddd-refactor/
├── plan.md              # Kế hoạch triển khai (file này)
├── research.md          # Nghiên cứu kiến trúc và quyết định kỹ thuật
├── data-model.md        # Mô hình thực thể miền, Value Objects và Domain Services
├── quickstart.md        # Hướng dẫn kiểm thử và xác thực
├── contracts/           # Hợp đồng giao tiếp (Agent events & SSE stream)
│   └── agent-events.md
└── checklists/          # Bảng kiểm tra chất lượng đặc tả
    └── requirements.md
```

### Source Code Layout

```text
backend/app/chatbot/
├── domain/
│   ├── entity.py                 # ChatSession, ChatMessage
│   ├── value_objects.py          # MessageRole, ToolCallRecord, AgentLoopState, ChatMessageMetadata, AgentStreamEvent
│   └── agent.py                  # [NEW] Domain Service Agent (ReAct Loop, Prompt Policy, Context Pruning)
├── application/
│   ├── send_chat_message_use_case.py   # [REFACTORED] Thin orchestrator
│   ├── get_chat_sessions_use_case.py
│   ├── get_session_messages_use_case.py
│   ├── delete_chat_session_use_case.py
│   └── get_quick_prompts_use_case.py
├── infrastructure/
│   ├── llm_client.py             # LLM Client Adapter
│   ├── repository.py             # ChatRepository
│   ├── models.py                 # ChatSessionModel, ChatMessageModel
│   └── tools/                    # Tool definitions and Registry
├── controller.py                 # FastAPI endpoints
├── providers.py                  # [UPDATED] Dishka DI provider for Agent & Use Case
└── schemas.py                    # API DTO schemas

backend/tests/unit/
└── test_chatbot.py               # [UPDATED] Unit tests for Agent and refactored Use Case
```

**Structure Decision**: Cấu trúc tuân thủ mô hình thư mục domain tiêu chuẩn của dự án `backend/app/chatbot/`, bổ sung file `domain/agent.py` và tái cấu trúc `application/send_chat_message_use_case.py` cùng `providers.py`.

## Complexity Tracking

> Không có vi phạm Constitution nào cần biện minh (Không có mục nào phát sinh ngoại lệ).
