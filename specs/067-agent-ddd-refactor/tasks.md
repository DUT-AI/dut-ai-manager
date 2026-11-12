---
description: "Task list for Chatbot Agent DDD Refactor implementation"
---

# Tasks: Chatbot Agent DDD Refactor

**Input**: Design documents from `specs/067-agent-ddd-refactor/`
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/agent-events.md](contracts/agent-events.md)

## Format: `- [ ] [TaskID] [P?] [Story?] Description with file path`

- **[P]**: Can run in parallel (different files, no direct dependencies)
- **[Story]**: Mapped user story from spec.md ([US1], [US2], [US3])
- Exact file paths included in every task

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Chuẩn bị cấu trúc file và Value Object cần thiết cho tầng Domain

- [x] T001 Tạo file mới cho Domain Service `Agent` tại `backend/app/chatbot/domain/agent.py`
- [x] T002 [P] Định nghĩa `AgentStreamEvent` và re-export các Value Objects trong `backend/app/chatbot/domain/value_objects.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Nền tảng chỉ thị nghiệp vụ và cấu hình Dependency Injection bắt buộc trước khi triển khai Use Case

- [x] T003 Đóng gói hằng số chỉ thị nghiệp vụ `DUT_ASSISTANT_SYSTEM_PROMPT` trong `backend/app/chatbot/domain/agent.py`
- [x] T004 Cấu hình Dishka provider cho `Agent` độc lập trong `backend/app/chatbot/providers.py`

**Checkpoint**: Nền tảng Domain Service đã sẵn sàng để triển khai User Stories.

---

## Phase 3: User Story 1 - Tách biệt nhiệm vụ điều phối của Use Case và logic vòng lặp Agent (Priority: P1) 🎯 MVP

**Goal**: Chuyển toàn bộ vòng lặp ReAct, gọi công cụ, và chống lặp vào `Agent`, đưa `SendChatMessageUseCase` về dạng Orchestrator mỏng.

**Independent Test**: Gửi câu hỏi cần gọi công cụ hoặc câu hỏi thường; Use Case nhận request, lưu User Message, chạy `Agent.run_stream`, lưu Assistant Message và phát đầy đủ các sự kiện SSE (`session_created`, `iteration_step`, `tool_call_start`, `tool_call_end`, `reasoning`, `content`, `done`).

### Tests for User Story 1 ⚠️

- [x] T005 [P] [US1] Tạo unit test cho `Agent.run_stream` trong `backend/tests/unit/test_chatbot_agent.py` kiểm tra sinh đầy đủ các events và `ChatMessageMetadata`

### Implementation for User Story 1

- [x] T006 [US1] Triển khai phương thức `run_stream`, vòng lặp ReAct, phân tích cú pháp delta/usage/timings, và chống lặp `add_call_signature` trong `Agent` tại `backend/app/chatbot/domain/agent.py`
- [x] T007 [US1] Refactor `SendChatMessageUseCase` tại `backend/app/chatbot/application/send_chat_message_use_case.py` thành Orchestrator mỏng (< 100 dòng), ủy quyền chu trình reasoning cho `Agent` và ánh xạ `AgentStreamEvent` sang SSE stream
- [x] T008 [US1] Cập nhật Dishka provider để inject `Agent` vào `SendChatMessageUseCase` tại `backend/app/chatbot/providers.py`

**Checkpoint**: User Story 1 hoàn tất - Use Case chỉ đóng vai trò điều phối, toàn bộ logic vòng lặp nằm trong Domain Service `Agent`.

---

## Phase 4: User Story 2 - Đóng gói chính sách quản lý ngữ cảnh và cắt tỉa Token trong Domain (Priority: P2)

**Goal**: Đóng gói thuật toán quản lý context window và nén kết quả công cụ cũ khi vượt ngưỡng 50k token vào Domain Service `Agent`.

**Independent Test**: Chạy unit test kiểm tra `_prune_context_if_needed` với danh sách message vượt ngưỡng 50,000 token, xác nhận chỉ kết quả công cụ cũ bị nén mà không ảnh hưởng tin nhắn user/system.

### Tests for User Story 2 ⚠️

- [x] T009 [P] [US2] Viết unit test xác minh nén ngữ cảnh khi vượt ngưỡng token trong `backend/tests/unit/test_chatbot_agent.py`

### Implementation for User Story 2

- [x] T010 [US2] Triển khai phương thức `_prune_context_if_needed` và `_count_tokens` trong `Agent` tại `backend/app/chatbot/domain/agent.py`
- [x] T011 [US2] Loại bỏ hoàn toàn phương thức `_estimate_tokens` và `_prune_context_history_if_needed` khỏi `backend/app/chatbot/application/send_chat_message_use_case.py`

**Checkpoint**: Toàn bộ logic quản lý token và context window đã nằm trọn vẹn trong Domain layer.

---

## Phase 5: User Story 3 - Bảo toàn tính toàn vẹn và tính tương thích ngược của Chatbot API & UI (Priority: P3)

**Goal**: Đảm bảo 100% các bài test chatbot backend và bản build frontend đều vượt qua mà không có bất kỳ lỗi hồi quy nào.

**Independent Test**: Chạy toàn bộ test suite `pytest` và lệnh `npm run build`, không có bất kỳ lỗi hay cảnh báo hồi quy.

### Implementation for User Story 3

- [x] T012 [P] [US3] Cập nhật các mock và test case trong `backend/tests/unit/test_chatbot.py` để tương thích với `Agent` injection mới
- [x] T013 [US3] Chạy và xác thực toàn bộ unit test backend qua lệnh `poetry run pytest tests/unit/test_chatbot.py tests/unit/test_database_tools.py`
- [x] T014 [US3] Xác thực tính toàn vẹn và hợp đồng client qua lệnh `npm run build` trong `frontend/`

**Checkpoint**: Tất cả các kịch bản kiểm thử đa bước, chống trùng lặp công cụ và build frontend đều vượt qua 100%.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Đảm bảo tiêu chuẩn code sạch, format và kiểm tra tài liệu xác thực

- [x] T015 [P] Kiểm tra linter và format mã nguồn backend qua `poetry run ruff check app/ tests/`
- [x] T016 Thực thi các bước xác thực trong `specs/067-agent-ddd-refactor/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Bắt đầu ngay, không có phụ thuộc.
- **Foundational (Phase 2)**: Phụ thuộc vào Phase 1 hoàn thành.
- **User Story 1 (Phase 3 - MVP)**: Phụ thuộc vào Phase 2 hoàn thành.
- **User Story 2 (Phase 4)**: Có thể thực hiện song song hoặc tiếp nối ngay sau User Story 1.
- **User Story 3 (Phase 5)**: Phụ thuộc vào User Story 1 & 2 hoàn thành.
- **Polish (Phase 6)**: Phụ thuộc vào toàn bộ các User Story hoàn tất.

### Parallel Opportunities

- `T002` có thể làm song song với `T001`.
- `T005` (unit test US1) có thể viết song song với cấu trúc `Agent`.
- `T009` (unit test US2) có thể viết song song với `T006`/`T007`.
- `T012` có thể cập nhật song song với `T010`/`T011`.
- `T015` có thể chạy song song ở bước hoàn tất.

---

## Implementation Strategy

### MVP First (User Story 1)
1. Hoàn thành Phase 1 & Phase 2.
2. Triển khai Phase 3: Xây dựng `Agent.run_stream`, refactor `SendChatMessageUseCase` thành Orchestrator.
3. Chạy test `test_chatbot_agent.py` để kiểm chứng MVP hoạt động độc lập.

### Incremental Delivery
1. Đưa `ContextPruningPolicy` vào `Agent` (User Story 2).
2. Tinh chỉnh bộ test `test_chatbot.py` và chạy full regression test (User Story 3).
3. Format mã nguồn và hoàn tất feature.
