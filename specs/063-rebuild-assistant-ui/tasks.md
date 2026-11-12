# Tasks: Tái Thiết Toàn Diện Giao Diện Trợ Lý Ảo (AI Assistant) Chuẩn shadcn AI Elements

**Input**: Design documents from `/specs/063-rebuild-assistant-ui/` (`spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/assistant-ui-contracts.ts`, `quickstart.md`)  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`  
**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Có thể chạy song song (các tệp khác nhau, không có quan hệ phụ thuộc lẫn nhau)
- **[Story]**: Gắn nhãn User Story tương ứng (`[US1]`, `[US2]`, `[US3]`, `[US4]`, `[US5]`)
- Mô tả công việc luôn chứa đường dẫn tệp cụ thể (Exact File Path)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Chuẩn bị nền tảng hạ tầng chia sẻ, rà soát component shadcn/ui nguyên tử và chuẩn hóa types.

- [X] T001 Rà soát và kiểm tra các thành phần shadcn/ui nguyên tử (`trace.tsx`, `message-scroller.tsx`, `bubble.tsx`, `code-block.tsx`, `dialog.tsx`, `button.tsx`) trong `frontend/src/components/ui/` để đảm bảo đầy đủ các export cần thiết.
- [X] T002 Cập nhật tệp định nghĩa kiểu dữ liệu `frontend/src/features/chatbot/types/chatbot.types.ts` để bổ sung các kiểu trạng thái UI và nhóm phiên hội thoại (`ChatSessionGroup`) theo đặc tả `specs/063-rebuild-assistant-ui/data-model.md`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Xây dựng các hạ tầng dùng chung cốt lõi bắt buộc phải hoàn thành trước khi triển khai các User Story.

**⚠️ CRITICAL**: Không bắt đầu triển khai các User Story cho đến khi giai đoạn này hoàn tất.

- [X] T003 [P] Xây dựng bộ kết xuất văn bản Markdown tích hợp khối mã nguồn Shiki và nút sao chép trong `frontend/src/features/chatbot/components/ai-elements/MarkdownRenderer.tsx`.
- [X] T004 [P] Cập nhật hook `frontend/src/features/chatbot/hooks/useChatbot.ts` để loại bỏ thông báo `antd` `antMessage`, chuyển sang cơ chế quản lý lỗi nội bộ và tối ưu hóa xử lý Server-Sent Events (SSE).
- [X] T005 [P] Cập nhật hook `frontend/src/features/chatbot/hooks/useChatSessions.ts` để loại bỏ `antd` `message`, tối ưu hóa các mutation xóa và làm mới danh sách phiên.

**Checkpoint**: Nền tảng chia sẻ đã sẵn sàng - việc triển khai các User Story có thể bắt đầu.

---

## Phase 3: User Story 1 - Trải nghiệm hội thoại trực quan & mượt mà với Chat Stream (Priority: P1) 🎯 MVP

**Goal**: Xây dựng lại khung trò chuyện cốt lõi với khả năng tự động bám đáy khi streaming, hiển thị bong bóng tin nhắn người dùng (`Bubble`) và thanh nhập liệu tự dãn nở (`PromptInput`).

**Independent Test**: Truy cập `http://localhost:5173/dashboard/assistant`, nhập câu hỏi và quan sát bong bóng câu hỏi xuất hiện bên phải, câu trả lời streaming xuất hiện bên trái với `MessageScroller` tự động bám đáy mượt mà; nút gửi chuyển sang icon spinner khi đang tải và tự mở lại khi hoàn thành.

### Implementation for User Story 1

- [X] T006 [P] [US1] Xây dựng thành phần khung nhập liệu tự dãn nở `frontend/src/features/chatbot/components/ai-elements/PromptInput.tsx` với phím tắt `Enter` gửi tin, `Shift+Enter` xuống dòng, và nút gửi chuyển icon `Loader2Icon` vô hiệu hóa khi streaming.
- [X] T007 [P] [US1] Tái cấu trúc thành phần tin nhắn `frontend/src/features/chatbot/components/ai-elements/Message.tsx` sử dụng `@/components/ui/bubble` căn lề phải cho người dùng và căn lề trái hiển thị markdown cho trợ lý.
- [X] T008 [US1] Xây dựng lại thành phần cuộn tin nhắn thông minh `frontend/src/features/chatbot/components/ai-elements/Chat.tsx` trên nền tảng `MessageScroller`, tự động bám đáy khi stream và tạm ngắt khi cuộn ngược lên.
- [X] T009 [US1] Tái cấu trúc `frontend/src/features/chatbot/components/ChatWindow.tsx` để điều phối `Chat` và `PromptInput` với độ rộng tối ưu (`max-w-3xl`) và bố cục tập trung.

**Checkpoint**: User Story 1 (MVP) đã hoàn chỉnh và có thể hoạt động độc lập.

---

## Phase 4: User Story 2 - Minh bạch hóa tư duy suy luận & Gọi công cụ (Priority: P1)

**Goal**: Hiển thị sinh động quá trình suy luận (Reasoning / Chain of Thought) và các bước thực thi công cụ (Tool Calls) dưới dạng các khối Trace Accordion mở rộng/thu gọn mượt mà.

**Independent Test**: Gửi câu hỏi yêu cầu tra cứu công cụ (ví dụ: *"Kiểm tra vi phạm tháng này của tôi"*), kiểm tra khối Reasoning hiển thị trạng thái "Thinking..." và tự chuyển thành "Thought" thu gọn; khối ToolTrace hiển thị tên công cụ và tham số JSON có định dạng.

### Implementation for User Story 2

- [X] T010 [P] [US2] Xây dựng lại khối tư duy suy luận `frontend/src/features/chatbot/components/ai-elements/Reasoning.tsx` sử dụng `TraceCollapsible`, `TraceLine`, `TraceIcon` với hiệu ứng chữ shimmer khi đang suy luận và thu gọn thành "Thought" khi xong.
- [X] T011 [P] [US2] Xây dựng lại khối thực thi công cụ `frontend/src/features/chatbot/components/ai-elements/ToolTrace.tsx` sử dụng `Trace` và `CodeBlock` hiển thị tên công cụ, trạng thái thực thi và tham số đầu vào.
- [X] T012 [US2] Tích hợp `Reasoning` và `ToolTrace` vào cấu trúc lượt tin nhắn trợ lý trong `frontend/src/features/chatbot/components/ai-elements/Message.tsx` nằm ngay phía trên nội dung văn bản markdown.

**Checkpoint**: Cả User Story 1 và User Story 2 đều hoạt động đồng bộ và minh bạch.

---

## Phase 5: User Story 3 - Quản trị phiên hội thoại & Lịch sử trò chuyện chuyên nghiệp (Priority: P2)

**Goal**: Xây dựng thanh bên quản lý 5 phiên gần nhất có thể thu gọn linh hoạt (Collapsible Sidebar), gom nhóm theo ngày, và xóa phiên bằng hộp thoại shadcn `Dialog`.

**Independent Test**: Bấm nút ẩn/hiện thanh bên trên thanh Header để kiểm tra cơ chế thu gọn trên desktop; mở hộp thoại xóa phiên và kiểm tra `DeleteSessionDialog` hiển thị xác nhận chuẩn shadcn.

### Implementation for User Story 3

- [X] T013 [P] [US3] Xây dựng hộp thoại xác nhận xóa phiên trò chuyện `frontend/src/features/chatbot/components/DeleteSessionDialog.tsx` sử dụng shadcn `Dialog`, `DialogHeader`, `DialogFooter` và `Button` thay thế hoàn toàn `Popconfirm` của Ant Design.
- [X] T014 [P] [US3] Xây dựng lại thanh bên quản lý phiên `frontend/src/features/chatbot/components/ChatSessionSidebar.tsx` với tính năng gom nhóm phiên theo thời gian (Hôm nay, Hôm qua, 7 ngày trước), nút tạo chat mới và biểu tượng mở modal xóa.
- [X] T015 [US3] Xây dựng thanh tiêu đề hội thoại `frontend/src/features/chatbot/components/ChatHeader.tsx` hiển thị avatar trợ lý, tên bot, nút toggle ẩn/hiện thanh bên (`PanelLeftClose` / `PanelLeft`) và nút bắt đầu chat mới.

**Checkpoint**: Quản trị phiên trò chuyện đã hoàn chỉnh, loại bỏ hoàn toàn các popup Ant Design cũ.

---

## Phase 6: User Story 4 - Gợi ý câu hỏi nhanh (Suggestions) (Priority: P2)

**Goal**: Cung cấp danh sách các thẻ câu hỏi gợi ý nhanh (Quick Prompts) thích ứng theo vai trò người dùng (Thành viên / Quản trị viên) khi bắt đầu phiên mới, bấm một chạm để gửi ngay.

**Independent Test**: Mở một phiên chat mới, thấy các thẻ gợi ý hiển thị đẹp mắt; bấm vào một thẻ thấy câu hỏi được gửi đi ngay và thẻ gợi ý tự ẩn sau 2 lượt chat.

### Implementation for User Story 4

- [X] T016 [US4] Tái cấu trúc thành phần gợi ý câu hỏi `frontend/src/features/chatbot/components/ai-elements/Suggestion.tsx` sử dụng shadcn `Card` / `Badge` với hiệu ứng hover tương tác và bố cục responsive.
- [X] T017 [US4] Tích hợp logic hiển thị thông minh cho `Suggestion` trong `frontend/src/features/chatbot/components/ChatWindow.tsx` (tự động ẩn khi cuộc trò chuyện có nhiều hơn 2 tin nhắn).

**Checkpoint**: Hệ thống gợi ý câu hỏi hoạt động mượt mà, giúp người dùng mới dễ dàng tiếp cận.

---

## Phase 7: User Story 5 - Thống nhất ngôn ngữ thiết kế thuần khiết & Điều phối cấp cao (Priority: P3)

**Goal**: Hoàn thiện trang điều phối chính `ChatbotPage.tsx`, loại bỏ hoàn toàn Ant Design khỏi toàn bộ chatbot module, đảm bảo tính tương thích responsive trên mobile và Dark/Light mode.

**Independent Test**: Chuyển đổi Dark/Light mode, kiểm tra giao diện không còn bất kỳ Ant Design component hay icon nào, kiểm tra thanh bên trượt mở dạng Sheet/Overlay trên màn hình di động.

### Implementation for User Story 5

- [X] T018 [US5] Tái cấu trúc trang điều phối `frontend/src/features/chatbot/pages/ChatbotPage.tsx` đóng vai trò Orchestrator quản lý trạng thái ẩn/hiện thanh bên, modal xóa phiên và kết nối các subcomponents.
- [X] T019 [US5] Cập nhật nút chat nổi `frontend/src/features/chatbot/components/FloatingChatButton.tsx` sử dụng biểu tượng Lucide React (`BotIcon`) và điều hướng trực tiếp vào `/dashboard/assistant`.
- [X] T020 [US5] Cập nhật tệp xuất danh mục component `frontend/src/features/chatbot/components/index.ts` để xuất sạch sẽ toàn bộ các subcomponents theo đúng Hiến pháp Nguyên tắc VIII.

**Checkpoint**: Toàn bộ module Chatbot đạt độ thuần nhất 100% về thiết kế.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Đảm bảo chất lượng toàn diện, loại bỏ triệt để mã cũ, kiểm tra kiểu tĩnh và xác minh thực tế.

- [X] T021 [P] Quét toàn bộ thư mục `frontend/src/features/chatbot/` để đảm bảo KHÔNG còn bất kỳ import nào từ `antd` hoặc `@ant-design/icons`.
- [X] T022 Chạy kiểm tra kiểu tĩnh TypeScript (`npm run typecheck` trong thư mục `frontend/`) và khắc phục mọi cảnh báo/lỗi liên quan.
- [X] T023 Chạy linter (`npm run lint` trong thư mục `frontend/`) để bảo đảm chất lượng code đạt chuẩn.
- [X] T024 Thực hiện kịch bản kiểm thử đầu-cuối theo tài liệu `specs/063-rebuild-assistant-ui/quickstart.md` trên cả kích thước màn hình Desktop và Mobile.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Không có phụ thuộc - thực thi ngay lập tức.
- **Foundational (Phase 2)**: Phụ thuộc vào Phase 1 - CHẶN toàn bộ các User Story tiếp theo.
- **User Story 1 (Phase 3 - P1 MVP)**: Phụ thuộc vào Phase 2.
- **User Story 2 (Phase 4 - P1)**: Phụ thuộc vào Phase 3 (tích hợp vào Message component).
- **User Story 3 (Phase 5 - P2)**: Phụ thuộc vào Phase 2.
- **User Story 4 (Phase 6 - P2)**: Phụ thuộc vào Phase 3 (tích hợp vào ChatWindow).
- **User Story 5 (Phase 7 - P3)**: Phụ thuộc vào việc hoàn tất các components của US1, US2, US3, US4.
- **Polish (Phase 8)**: Phụ thuộc vào việc hoàn tất toàn bộ các User Story.

### Parallel Opportunities

- **Phase 1**: T001 và T002 có thể thực thi song song.
- **Phase 2**: T003, T004, và T005 có thể thực thi song song (tác động vào các file độc lập).
- **Phase 3 (US1)**: T006 (`PromptInput`) và T007 (`Message`) có thể code song song trước khi ráp vào T008 (`Chat`) và T009 (`ChatWindow`).
- **Phase 4 (US2)**: T010 (`Reasoning`) và T011 (`ToolTrace`) có thể code song song.
- **Phase 5 (US3)**: T013 (`DeleteSessionDialog`) và T014 (`ChatSessionSidebar`) có thể code song song.
- **Phase 8 (Polish)**: T021 có thể chạy song song với chuẩn bị kiểm thử.

---

## Parallel Example: Foundational Phase

```bash
# Thực hiện đồng thời các tác vụ nền tảng độc lập tệp:
Task: "Xây dựng bộ kết xuất văn bản Markdown trong frontend/src/features/chatbot/components/ai-elements/MarkdownRenderer.tsx"
Task: "Cập nhật hook trong frontend/src/features/chatbot/hooks/useChatbot.ts"
Task: "Cập nhật hook trong frontend/src/features/chatbot/hooks/useChatSessions.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Focus)

1. Hoàn tất Phase 1: Setup
2. Hoàn tất Phase 2: Foundational (Bắt buộc)
3. Hoàn tất Phase 3: User Story 1
4. **Dừng lại & Xác minh**: Kiểm tra luồng chat streaming và ô nhập liệu hoạt động mượt mà độc lập.
5. Triển khai tiếp các User Story 2 → 3 → 4 → 5 theo thứ tự ưu tiên.
