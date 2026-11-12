# Implementation Plan: Tái Thiết Toàn Diện Giao Diện Trợ Lý Ảo (AI Assistant) Chuẩn shadcn AI Elements

**Branch**: `063-rebuild-assistant-ui` | **Date**: 2026-11-12 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/063-rebuild-assistant-ui/spec.md`

## Summary

Đập đi xây lại toàn bộ giao diện Trợ lý AI (`http://localhost:5173/dashboard/assistant`) theo các mẫu thiết kế agentic chuẩn của **shadcn AI Elements** (Chat, Message, MessageScroller, PromptInput, Reasoning, Tool Trace, Suggestion, Sidebar). Thay thế 100% các thành phần Ant Design chắp vá (`antd` Button, `Popconfirm`, `@ant-design/icons`) bằng các thành phần shadcn/ui nguyên tử (`trace`, `message-scroller`, `bubble`, `message`, `code-block`, `dialog`, `button`, `tooltip`) và bộ biểu tượng Lucide React, tạo nên một giao diện chatbot thông minh, mượt mà, phản hồi tốt và đạt chuẩn sản phẩm cao cấp.

---

## Technical Context

**Language/Version**: TypeScript 5.9+, React 19.2+  
**Primary Dependencies**: Tailwind CSS v4, `@shadcn/react`, `@base-ui/react`, `@radix-ui`, `lucide-react`, `react-markdown`, `shiki`, `@tanstack/react-query`  
**Storage**: N/A (Tầng giao diện kết nối API backend hiện có qua `chatbotService` và Server-Sent Events)  
**Testing**: TypeScript Typecheck (`npm run typecheck`), ESLint (`npm run lint`), Manual/Playwright E2E verification  
**Target Platform**: Trình duyệt Web hiện đại (Desktop, Tablet, Mobile responsive)  
**Project Type**: Single Page Application (Frontend feature module)  
**Performance Goals**: Thời gian render phản hồi đầu tiên < 300ms, cuộn bám đáy 60fps mượt mà, không giật màn hình khi stream, zero horizontal overflow  
**Constraints**:
- Loại bỏ hoàn toàn Ant Design (`antd`, `@ant-design/icons`) khỏi toàn bộ thư mục `frontend/src/features/chatbot/`
- Tuân thủ nghiêm ngặt Hiến pháp Nguyên tắc VIII (Frontend Component Modularity & Single-Responsibility UI)
- Giữ nguyên hợp đồng API backend và kiểu dữ liệu DTO từ `src/types/api.generated.d.ts`  
**Scale/Scope**: 1 trang điều phối (`ChatbotPage.tsx`), 1 thanh bên (`ChatSessionSidebar.tsx`), 1 hộp thoại xóa (`DeleteSessionDialog.tsx`), 1 thanh tiêu đề (`ChatHeader.tsx`), 1 cửa sổ chat (`ChatWindow.tsx`), và 7 thành phần AI Elements chuyên dụng trong `components/ai-elements/`

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc Hiến pháp | Trạng thái | Đánh giá & Tuân thủ |
|:---------------------|:-----------|:---------------------|
| **VIII. Frontend Component Modularity & Single-Responsibility UI (MUST)** | **PASS** | Tách bạch hoàn toàn: trang `ChatbotPage.tsx` chỉ đóng vai trò Orchestrator; toàn bộ UI được chia nhỏ thành các subcomponents độc lập trong `components/` và `components/ai-elements/`, tái xuất qua `index.ts`. Không có component nguyên khối. |
| **X. Zero Redundant Backward Compatibility & Contextual Field Ownership (MUST)** | **PASS** | Loại bỏ sạch sẽ các đoạn code style chắp vá cũ, refactor trực tiếp các component tiêu thụ, không tạo thêm wrapper bí danh thừa thãi. |
| **XI. Plain Text Notifications & Clean Channel Presentation (MUST)** | **PASS** | Các thông báo lỗi và thông báo trạng thái được trình bày dạng văn bản sạch, sử dụng hộp thoại xác nhận shadcn Dialog và icon Lucide. |
| **XV. Unified Client Networking & Fail-Fast Session Renewal (MUST)** | **PASS** | Tận dụng nguyên vẹn `chatbotService` và `axiosInstance` chuẩn của dự án, không gọi `fetch` tự phát. |

**Kết luận Gate**: ĐẠT 100% các tiêu chuẩn Hiến pháp.

---

## Project Structure

### Documentation (this feature)

```text
specs/063-rebuild-assistant-ui/
├── spec.md              # Đặc tả nghiệp vụ và kịch bản người dùng
├── checklists/
│   └── requirements.md  # Checklist chất lượng đặc tả (100% Pass)
├── plan.md              # Kế hoạch kỹ thuật & kiến trúc (Tệp này)
├── research.md          # Kết quả nghiên cứu kiến trúc shadcn AI Elements
├── data-model.md        # Mô hình trạng thái giao diện & phân rã component
├── quickstart.md        # Hướng dẫn kiểm thử và xác minh đầu-cuối
└── contracts/
    └── assistant-ui-contracts.ts # Hợp đồng kiểu dữ liệu component & SSE events
```

### Source Code (Cấu trúc mã nguồn triển khai)

```text
frontend/src/features/chatbot/
├── components/
│   ├── ai-elements/
│   │   ├── Chat.tsx              # Viewport danh sách tin nhắn bám đáy với MessageScroller
│   │   ├── Message.tsx           # Lượt tin nhắn (User Bubble / Assistant Markdown)
│   │   ├── PromptInput.tsx       # Khung nhập liệu tự dãn nở, nút gửi chuyển spinner khi stream
│   │   ├── Reasoning.tsx         # Khối Trace Accordion (Thinking... -> Thought)
│   │   ├── ToolTrace.tsx         # Khối Trace hiển thị chi tiết các lần gọi công cụ
│   │   ├── Suggestion.tsx        # Danh sách thẻ câu hỏi gợi ý nhanh (Quick Prompts)
│   │   └── MarkdownRenderer.tsx  # Bộ render Markdown tích hợp CodeBlock Shiki & Copy button
│   ├── ChatHeader.tsx            # Thanh tiêu đề trên cùng: Avatar, Tên bot, Nút toggle sidebar, Nút tạo chat mới
│   ├── ChatSessionSidebar.tsx    # Thanh bên danh sách phiên gom nhóm theo ngày, hỗ trợ thu gọn
│   ├── DeleteSessionDialog.tsx   # Hộp thoại xác nhận xóa phiên chat dùng shadcn Dialog
│   ├── ChatWindow.tsx            # Khung điều phối trung tâm hội thoại
│   ├── FloatingChatButton.tsx    # Nút chat nổi toàn trang (chuyển hướng nhanh tới /dashboard/assistant)
│   └── index.ts                  # Re-export sạch sẽ toàn bộ subcomponents
├── hooks/
│   ├── useChatbot.ts             # Hook điều phối luồng chat, streaming SSE và tin nhắn
│   ├── useChatSessions.ts        # Hook truy vấn và quản lý 5 phiên chat gần nhất
│   └── index.ts
├── pages/
│   └── ChatbotPage.tsx           # Trang điều phối cấp cao (Orchestrator)
├── services/
│   └── chatbot.service.ts        # Service kết nối API backend & SSE
├── types/
│   └── chatbot.types.ts          # Định nghĩa kiểu dữ liệu thống nhất từ OpenAPI
└── index.ts
```

**Structure Decision**: Cấu trúc module frontend được chuẩn hóa tuyệt đối theo mô hình Feature-Driven kết hợp Clean UI Modularity. Toàn bộ logic hiển thị AI Elements được đóng gói chuyên biệt, cho phép mở rộng linh hoạt mà không ảnh hưởng đến các domain khác.

---

## Complexity Tracking

> Không có vi phạm Hiến pháp nào cần biện minh. Giải pháp sử dụng triệt để các component nguyên tử đã có trong dự án kết hợp với các mẫu thiết kế của shadcn AI Elements để giảm độ phức tạp và tăng tính bền vững của mã nguồn.
