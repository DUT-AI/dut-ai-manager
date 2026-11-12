# Research & Architecture Decisions: Tái Thiết Toàn Diện Giao Diện Trợ Lý Ảo (AI Assistant)

**Feature Branch**: `063-rebuild-assistant-ui`  
**Date**: 2026-11-12  
**Status**: Completed  

---

## 1. Triết Lý & Kiến Trúc AI Elements (shadcn/ui Composition)

### Quyết định (Decision)
Xây dựng bộ thành phần giao diện hội thoại thông minh trực tiếp trong thư mục `frontend/src/features/chatbot/components/ai-elements/` dựa trên việc hợp thành (composition) các thành phần nguyên tử có sẵn của shadcn/ui (`trace`, `message-scroller`, `bubble`, `message`, `code-block`, `dialog`, `button`, `badge`, `tooltip`, `collapsible`).

### Lý do lựa chọn (Rationale)
1. **Tuân thủ triết lý shadcn**: *"There is no package to install. The code is yours."* Việc sở hữu toàn bộ code component giúp dự án hoàn toàn làm chủ phong cách hiển thị, dễ dàng tùy biến giao diện phù hợp với thương hiệu DUT AI Manager mà không bị phụ thuộc vào các gói npm bên ngoài.
2. **Khắc phục triệt để lỗi giao diện chắp vá**: Trước đây giao diện bị lai tạp giữa Ant Design (`@ant-design/icons`, `antd` Button, `Popconfirm`) và Tailwind CSS tự viết, dẫn đến hiện tượng vỡ layout, phông chữ lệch chuẩn và cảm giác nghiệp dư. Chuyển sang 100% shadcn AI Elements giải quyết dứt điểm vấn đề này.
3. **Hiệu năng & Tương thích React 19**: Dự án sử dụng React 19 và Tailwind CSS v4. Các component shadcn nội bộ tương thích tối đa với `@base-ui/react` và `@radix-ui`, không gây cảnh báo xung đột runtime.

### Các phương án thay thế đã đánh giá (Alternatives Considered)
- **Cài đặt thư viện `@ai-sdk/react` hoặc `elements.ai-sdk.dev` qua npm**: Bị loại vì xung đột phiên bản dependency với React 19 và Tailwind v4 trong dự án, đồng thời hạn chế khả năng tinh chỉnh style tiếng Việt.
- **Giữ Ant Design và chỉ sửa style CSS**: Bị loại vì Ant Design có triết lý form/table truyền thống, không có sẵn các mẫu thiết kế agentic chuyên sâu (như Chain of Thought, Trace, Message Scroller, Tool Execution) khiến giao diện luôn thô và cồng kềnh.

---

## 2. Giải Pháp Cuộn Tin Nhắn Thông Minh (MessageScroller & Auto-Scroll)

### Quyết định (Decision)
Tận dụng component `frontend/src/components/ui/message-scroller.tsx` đã được cấu hình sẵn trong dự án với cơ chế:
- **Pin to Bottom**: Khi người dùng ở đáy khung chat hoặc tin nhắn đang streaming, scroller tự động bám đáy theo thời gian thực.
- **Scroll Lock Detection**: Khi người dùng chủ động lăn chuột ngược lên trên để đọc lại dữ liệu cũ, scroller tự động ngắt chế độ bám đáy để tránh giật màn hình.
- **Scroll to Bottom Button**: Hiển thị nút nổi tròn kèm biểu tượng mũi tên xuống (`ArrowDownIcon`) ở góc dưới khung chat khi khoảng cách tới đáy > 100px.

### Lý do lựa chọn (Rationale)
Trải nghiệm streaming văn bản đòi hỏi cơ chế quản lý viewport cực kỳ khắt khe. Nếu cuộn cưỡng bức, người dùng không thể đọc lại các đoạn trước. Nếu không cuộn tự động, người dùng không biết AI đang viết gì. `MessageScroller` giải quyết hài hòa cả hai nhu cầu này.

### Các phương án thay thế đã đánh giá (Alternatives Considered)
- **Tự viết `useEffect` với `element.scrollIntoView({ behavior: 'smooth' })`**: Thường gây giật màn hình trên các thiết bị cấu hình yếu khi streaming nhiều token/giây và cướp quyền điều khiển cuộn của người dùng.

---

## 3. Kiến Trúc Hiển Thị Tư Duy (Reasoning / Chain of Thought) và Thực Thi Công Cụ (Tool Trace)

### Quyết định (Decision)
Tất cả các bước trung gian của Agent (suy luận logic, gọi tool kiểm tra database) được quy chuẩn hóa trên nền tảng `Trace` (`@/components/ui/trace.tsx`):
1. **Khối Reasoning (`Reasoning.tsx`)**:
   - Dùng `TraceCollapsible` với `TraceLine`.
   - Trạng thái `running` (đang suy luận): Hiển thị icon spinner xoay (`Loader2Icon`), tiêu đề "Thinking..." với hiệu ứng chữ sáng mờ (shimmer).
   - Trạng thái hoàn tất: Chuyển thành icon tích tròn (`CircleCheckIcon`), tiêu đề "Thought", tự động thu gọn để không choán không gian đọc của câu trả lời chính, cho phép người dùng bấm để mở rộng xem toàn văn tư duy.
2. **Khối Tool Trace (`ToolTrace.tsx`)**:
   - Mỗi lần gọi công cụ được thể hiện thành một `TraceLine` có biểu tượng `TerminalIcon` hoặc `WrenchIcon`.
   - Hiển thị tên công cụ thân thiện (ví dụ: `inspect_entity_records` -> "Tra cứu thực thể học vụ").
   - Trạng thái: Đang thực thi (`running`) hoặc Đã hoàn thành (`success`).
   - Mở rộng hiển thị tham số truy vấn dưới dạng khối JSON format gọn gàng bằng `CodeBlock`.

### Lý do lựa chọn (Rationale)
Đưa toàn bộ bước "nghĩ" và "làm" của Agent vào cùng một ngôn ngữ thiết kế đồng nhất (Trace) theo đúng chuẩn shadcn AI Elements, giúp giao diện trực quan, khoa học và minh bạch.

---

## 4. Bố Cục Responsive & Thanh Bên Quản Trị Phiên (Collapsible Sidebar)

### Quyết định (Decision)
1. **Trên màn hình Desktop (`>= lg`)**:
   - Thanh bên quản lý phiên hội thoại (`ChatSessionSidebar.tsx`) có thể thu gọn (Collapsible) bằng nút bấm Panel Toggle trên thanh Header (`PanelLeftCloseIcon` / `PanelLeftIcon`).
   - Khi mở: Độ rộng ~260px, hiển thị danh sách phiên, nút tạo chat mới, nút xóa phiên.
   - Khi thu gọn: Khung chat chính tự động dãn nở chiếm trọn không gian, thanh header hiển thị nút mở lại thanh bên.
2. **Trên màn hình Mobile / Tablet (`< lg`)**:
   - Thanh bên ẩn mặc định, mở ra dạng Sheet/Drawer phủ mờ nền (Backdrop overlay) khi người dùng chạm vào nút menu ở góc trái trên.
3. **Nhóm phiên trò chuyện**:
   - Tự động gom nhóm các phiên chat theo mốc thời gian: "Hôm nay", "Hôm qua", "7 ngày trước" để tăng tính ngăn nắp.
4. **Hộp thoại xác nhận xóa phiên**:
   - Thay thế toàn bộ `Popconfirm` của Ant Design bằng component `Dialog` (`frontend/src/components/ui/dialog.tsx`) chuẩn shadcn.

### Lý do lựa chọn (Rationale)
Tối ưu hóa diện tích hiển thị trên các thiết bị khác nhau, đồng thời tuân thủ cam kết loại bỏ 100% Ant Design khỏi module chatbot.

---

## 5. Kết Xuất Văn Bản Markdown & Khối Mã Nguồn (Code Block)

### Quyết định (Decision)
Sử dụng `react-markdown` kết hợp với `CodeBlock` (`frontend/src/components/ui/code-block.tsx`):
- Các đoạn code inline hiển thị trong thẻ `<code>` bo góc tinh tế.
- Các đoạn code block nhiều dòng tự động chuyển thành `<CodeBlock>` chuẩn shadcn có:
  - Thanh header hiển thị tên ngôn ngữ lập trình.
  - Nút Copy to Clipboard với biểu tượng sao chép / tích xanh xác nhận.
  - Nền tối tương thích cả Light mode và Dark mode.

### Lý do lựa chọn (Rationale)
Giúp các câu trả lời chứa code, SQL query hoặc bảng biểu trở nên đẹp mắt, dễ đọc và thao tác sao chép tức thì chỉ với một cú nhấp chuột.
