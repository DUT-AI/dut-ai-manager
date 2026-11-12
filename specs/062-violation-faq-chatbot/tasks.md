# Tasks: Chatbot Trợ Lý Giải Đáp Vi Phạm & Vận Hành Cho Thành Viên và Ban Quản Trị

**Input**: Design documents from `specs/062-violation-faq-chatbot/`  
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/chat-api.yaml](./contracts/chat-api.yaml)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Khởi tạo cấu hình môi trường, thư mục và tệp tri thức quy chế dùng chung

- [x] T001 Cấu hình biến môi trường `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY` trong `backend/app/core/config.py`
- [x] T002 [P] Tạo cấu trúc thư mục module `backend/app/chatbot/{domain,application,infrastructure/knowledge}`
- [x] T003 [P] Tạo cấu trúc thư mục module `frontend/src/features/chatbot/{components,pages,hooks,services,types}`
- [x] T004 [P] Biên soạn tài liệu nội quy quy chế chuẩn hóa trong `backend/app/chatbot/infrastructure/knowledge/violation_policies.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Xây dựng hạ tầng dữ liệu cốt lõi, ORM models, migration, repository, client LLM và types

**⚠️ CRITICAL**: Các User Stories phía sau phụ thuộc hoàn toàn vào hạ tầng này

- [x] T005 [P] Định nghĩa Value Objects `MessageRole`, `ChatMessageMetadata`, `ToolCallRecord` trong `backend/app/chatbot/domain/value_objects.py`
- [x] T006 [P] Định nghĩa Domain Entities `ChatSession`, `ChatMessage` trong `backend/app/chatbot/domain/entity.py`
- [x] T007 Định nghĩa SQLAlchemy ORM Models `ChatSessionModel` và `ChatMessageModel` (UTC timestamps, PydanticType metadata, cascade delete) trong `backend/app/chatbot/infrastructure/models.py`
- [x] T008 Tạo và chạy Alembic migration cho bảng `chat_sessions` và `chat_messages` trong `backend/alembic/versions/`
- [x] T009 Triển khai `ChatRepository` với cơ chế FIFO tự động xóa phiên cũ nhất khi vượt quá 5 phiên trong `backend/app/chatbot/infrastructure/repository.py`
- [x] T010 Triển khai `LLMClient` bất đồng bộ kết nối `https://llm2.dutai.site/v1` hỗ trợ streaming SSE trong `backend/app/chatbot/infrastructure/llm_client.py`
- [x] T011 [P] Định nghĩa Pydantic Request/Response DTOs trong `backend/app/chatbot/schemas.py`
- [x] T012 Đăng ký Dishka Provider cho `ChatRepository`, `LLMClient`, `ChatbotToolRegistry` và các Use Cases trong `backend/app/chatbot/providers.py` và tích hợp vào `backend/app/main.py`
- [x] T013 [P] Định nghĩa TypeScript types và API interfaces trong `frontend/src/features/chatbot/types/chatbot.types.ts`
- [x] T014 [P] Triển khai `ChatbotService` với client Axios và hàm đọc SSE ReadableStream trong `frontend/src/features/chatbot/services/chatbot.service.ts`
- [x] T015 Triển khai hook `useChatSessions` với React Query để quản lý danh sách tối đa 5 phiên trong `frontend/src/features/chatbot/hooks/useChatSessions.ts`

**Checkpoint**: Nền tảng dữ liệu, ORM, LLM client và API service đã sẵn sàng để triển khai các User Story.

---

## Phase 3: User Story 1 - Thành viên tra cứu & giải thích lý do vi phạm của chính mình (Priority: P1) 🎯 MVP

**Goal**: Thành viên đăng nhập có thể trò chuyện với chatbot để tra cứu và giải thích chi tiết các vi phạm của chính mình, bảo mật IDOR 100%, truyền dữ liệu dạng SSE stream mượt mà trên cả trang `/assistant` và nút nổi Floating Icon.

**Independent Test**: Đăng nhập tài khoản thành viên có vi phạm, hỏi "Tại sao tôi bị phạt ngày gần nhất?", nhận được phản hồi stream giải thích đúng vi phạm cá nhân theo dữ liệu thực tế từ database.

### Implementation for User Story 1

- [ ] T016 [US1] Triển khai công cụ `get_my_violations` (khóa cứng theo `current_user.id`) trong `backend/app/chatbot/infrastructure/tools_registry.py`
- [ ] T017 [US1] Triển khai Use Case `SendChatMessageUseCase` (quản lý ngữ cảnh phiên, gọi Tool, sinh phản hồi SSE) trong `backend/app/chatbot/application/send_chat_message_use_case.py`
- [ ] T018 [P] [US1] Triển khai Use Case `GetChatSessionsUseCase` (lấy tối đa 5 phiên) trong `backend/app/chatbot/application/get_chat_sessions_use_case.py`
- [ ] T019 [P] [US1] Triển khai Use Case `GetSessionMessagesUseCase` trong `backend/app/chatbot/application/get_session_messages_use_case.py`
- [ ] T020 [P] [US1] Triển khai Use Case `DeleteChatSessionUseCase` trong `backend/app/chatbot/application/delete_chat_session_use_case.py`
- [ ] T021 [US1] Triển khai FastAPI Controller với các endpoints `POST /chat`, `GET /sessions`, `GET /sessions/{id}/messages`, `DELETE /sessions/{id}` trong `backend/app/chatbot/controller.py`
- [ ] T022 [P] [US1] Triển khai pattern `Message.tsx` (shadcn/ui AI Elements) hiển thị tin nhắn turn-based và render markdown stream bằng `react-markdown` trong `frontend/src/features/chatbot/components/ai-elements/Message.tsx`
- [ ] T023 [P] [US1] Triển khai pattern `Chat.tsx` (shadcn/ui AI Elements) quản lý luồng tin nhắn và tự động cuộn (Message Scroller) trong `frontend/src/features/chatbot/components/ai-elements/Chat.tsx`
- [ ] T024 [P] [US1] Triển khai pattern `PromptInput.tsx` (shadcn/ui AI Elements) với tự động dãn dòng, phím tắt Enter và trạng thái gửi trong `frontend/src/features/chatbot/components/ai-elements/PromptInput.tsx`
- [ ] T025 [P] [US1] Triển khai pattern `Reasoning.tsx` (shadcn/ui AI Elements) dạng collapsible hiển thị quá trình suy luận `reasoning_content` của mô hình Gemma trong `frontend/src/features/chatbot/components/ai-elements/Reasoning.tsx`
- [ ] T026 [P] [US1] Triển khai component `ChatSessionSidebar.tsx` hiển thị tối đa 5 phiên và nút tạo mới/xóa phiên trong `frontend/src/features/chatbot/components/ChatSessionSidebar.tsx`
- [ ] T027 [US1] Triển khai hook `useChatbot.ts` quản lý gửi tin nhắn, đọc luồng SSE chunk by chunk và cập nhật state trong `frontend/src/features/chatbot/hooks/useChatbot.ts`
- [ ] T028 [US1] Xây dựng trang toàn màn hình `ChatbotPage.tsx` gắn route `/assistant` trong `frontend/src/features/chatbot/pages/ChatbotPage.tsx`
- [ ] T029 [US1] Xây dựng `FloatingChatButton.tsx` (nút tròn nổi góc dưới phải màn hình kèm Popover/Drawer chat) trong `frontend/src/features/chatbot/components/FloatingChatButton.tsx`
- [ ] T030 [US1] Tích hợp route `/assistant` vào thanh điều hướng và nhúng `FloatingChatButton` vào layout chính (`MainLayout.tsx`) trong `frontend/src/`

**Checkpoint**: Hoàn tất User Story 1 (MVP) - Thành viên có thể tra cứu và giải thích vi phạm của bản thân mượt mà trên web.

---

## Phase 4: User Story 2 - Ban Quản trị / Mentor tra cứu tổng hợp & giám sát học vụ (Priority: P2)

**Goal**: Người dùng có quyền quản trị (`violation:read`, `homework:read`, `meeting:read`) có thể truy vấn số liệu tổng hợp vi phạm toàn hệ thống, danh sách vắng họp không phép và thành viên chưa nộp bài tập sát deadline.

**Independent Test**: Đăng nhập tài khoản Admin/Trainer, hỏi "Tổng hợp vi phạm tuần này" hoặc "Ai chưa nộp bài tập mới nhất?", nhận được danh sách tổng hợp chính xác; tài khoản Member thông thường hỏi sẽ bị từ chối truy cập.

### Implementation for User Story 2

- [ ] T031 [P] [US2] Triển khai công cụ quản trị `admin_summarize_violations` (thống kê theo tuần/tháng, lọc người có $\ge 3$ vi phạm) trong `backend/app/chatbot/infrastructure/tools_registry.py`
- [ ] T032 [P] [US2] Triển khai công cụ quản trị `admin_get_unsubmitted_homeworks` (danh sách học viên chưa nộp bài tập) trong `backend/app/chatbot/infrastructure/tools_registry.py`
- [ ] T033 [P] [US2] Triển khai công cụ quản trị `admin_get_meeting_absentees` (danh sách vắng họp không phép) trong `backend/app/chatbot/infrastructure/tools_registry.py`
- [ ] T034 [US2] Triển khai cơ chế kiểm tra quyền hạn (Permission Guard) trong `tools_registry.py` đảm bảo chỉ nạp và thực thi công cụ quản trị khi người dùng có quyền hợp lệ
- [ ] T035 [US2] Triển khai Use Case `GetQuickPromptsUseCase` trả về gợi ý nhanh thích ứng theo vai trò trong `backend/app/chatbot/application/get_quick_prompts_use_case.py`
- [ ] T036 [US2] Bổ sung endpoint `GET /api/v1/chatbot/quick-prompts` trong `backend/app/chatbot/controller.py`
- [ ] T037 [P] [US2] Triển khai pattern `Suggestion.tsx` (shadcn/ui AI Elements) cho danh sách chip câu hỏi gợi ý nhanh trong `frontend/src/features/chatbot/components/ai-elements/Suggestion.tsx`
- [ ] T038 [P] [US2] Triển khai pattern `ToolTrace.tsx` (shadcn/ui AI Elements) hiển thị trạng thái và kết quả gọi công cụ ngầm trong `frontend/src/features/chatbot/components/ai-elements/ToolTrace.tsx`

**Checkpoint**: Ban Quản trị và Mentor có thể truy vấn báo cáo tổng hợp và giám sát học vụ tức thì qua chatbot.

---

## Phase 5: User Story 3 - Hỏi đáp chính sách & quy chế vi phạm chung (Priority: P2)

**Goal**: Thành viên và ban quản trị có thể hỏi đáp các quy định, biểu phí phạt, giờ giấc điểm danh, quy chế xin phép và nhận được trích dẫn chính xác từ tài liệu quy chế.

**Independent Test**: Hỏi "Đến muộn bao nhiêu phút thì bị tính là trễ?", bot trích dẫn đúng quy chế thời gian từ file nội quy `violation_policies.md`.

### Implementation for User Story 3

- [ ] T039 [US3] Triển khai công cụ `get_violation_policies` nạp nội dung quy chế từ `violation_policies.md` trong `backend/app/chatbot/infrastructure/tools_registry.py`
- [ ] T040 [US3] Tinh chỉnh System Prompt trong `backend/app/chatbot/infrastructure/llm_client.py` để trích xuất điều khoản và giải thích quy chế súc tích, dễ hiểu

---

## Phase 6: User Story 4 - Hướng dẫn liên hệ HR khi có thắc mắc hoặc cần giải trình (Priority: P3)

**Goal**: Đảm bảo bot giữ đúng vai trò Read-only Advisor; khi thành viên có thắc mắc hoặc khiếu nại về vi phạm, bot hướng dẫn rõ ràng việc liên hệ trực tiếp với bộ phận HR mà không tự động sửa đổi dữ liệu hay chèn liên kết phức tạp.

**Independent Test**: Thành viên gửi câu hỏi "Tôi đã xin phép rồi sao vẫn bị phạt?", bot giải thích thông tin ghi nhận trong hệ thống và hướng dẫn liên hệ trực tiếp HR.

### Implementation for User Story 4

- [ ] T041 [US4] Cấu hình nguyên tắc ứng xử cố vấn chỉ đọc (Read-only Advisor Guidelines) trong prompt của `backend/app/chatbot/infrastructure/llm_client.py` hướng dẫn liên hệ HR khi phát hiện sai lệch

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Tinh chỉnh giao diện, rate limiting, kiểm thử toàn diện và tài liệu hóa

- [ ] T042 [P] Áp dụng Rate Limiting bảo vệ endpoint chat trong `backend/app/chatbot/controller.py`
- [ ] T043 [P] Xuất khẩu sạch sẽ các components qua `frontend/src/features/chatbot/components/index.ts` và `frontend/src/features/chatbot/index.ts`
- [ ] T044 Chạy kiểm thử xác thực toàn diện theo các kịch bản trong `specs/062-violation-faq-chatbot/quickstart.md`
- [ ] T045 Kiểm tra chất lượng mã nguồn backend và frontend (`ruff check backend`, `npm run typecheck`)

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)**: Không có phụ thuộc, thực hiện ngay lập tức.
- **Foundational (Phase 2)**: Phụ thuộc vào Phase 1; **BẮT BUỘC** hoàn thành trước khi code các User Story.
- **User Story 1 (Phase 3 - MVP)**: Phụ thuộc vào Phase 2. Cung cấp chức năng chat cá nhân cốt lõi.
- **User Story 2 (Phase 4)**: Phụ thuộc vào Phase 2 và tích hợp vào controller/UI của Phase 3.
- **User Story 3 (Phase 5)**: Phụ thuộc vào Phase 2 và Phase 3.
- **User Story 4 (Phase 6)**: Phụ thuộc vào Phase 3 (tinh chỉnh prompt).
- **Polish (Phase 7)**: Thực hiện sau khi các User Stories đã hoàn tất.

### Parallel Opportunities
- Các task đánh dấu `[P]` trong cùng một Phase có thể chạy song song (do tác động trên các file khác nhau, không xung đột).
- Sau khi hoàn thành Phase 2, backend tools và frontend components của User Story 1 có thể phát triển song song.

---

## Parallel Example: User Story 1

```bash
# Triển khai song song các subcomponent frontend:
Task: "ChatMessageItem.tsx trong frontend/src/features/chatbot/components/ChatMessageItem.tsx"
Task: "ChatMessageList.tsx trong frontend/src/features/chatbot/components/ChatMessageList.tsx"
Task: "ChatInput.tsx trong frontend/src/features/chatbot/components/ChatInput.tsx"
Task: "ChatSessionSidebar.tsx trong frontend/src/features/chatbot/components/ChatSessionSidebar.tsx"

# Triển khai song song các Use Cases độc lập backend:
Task: "GetChatSessionsUseCase trong backend/app/chatbot/application/get_chat_sessions_use_case.py"
Task: "GetSessionMessagesUseCase trong backend/app/chatbot/application/get_session_messages_use_case.py"
Task: "DeleteChatSessionUseCase trong backend/app/chatbot/application/delete_chat_session_use_case.py"
```

---

## Implementation Strategy

### MVP First (User Story 1)
1. Hoàn thành **Phase 1** (Setup) & **Phase 2** (Foundational).
2. Hoàn thành **Phase 3** (User Story 1): Thành viên chat giải đáp vi phạm cá nhân với SSE streaming.
3. **Nghiệm thu MVP**: Xác thực hoạt động tra cứu vi phạm cá nhân trên cả trang `/assistant` và nút nổi.

### Incremental Delivery
1. **MVP**: Hoàn tất User Story 1 (Thành viên tra cứu vi phạm của mình).
2. **Increment 2**: Bổ sung User Story 2 (Ban Quản trị truy vấn tổng hợp vi phạm, vắng họp, bài tập).
3. **Increment 3**: Bổ sung User Story 3 & 4 (Tra cứu quy chế và hướng dẫn liên hệ HR).
4. **Final Polish**: Rate limiting, kiểm thử tải và dọn dẹp mã nguồn.
