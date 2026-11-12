# Feature Specification: Tái Thiết Toàn Diện Giao Diện Trợ Lý Ảo (AI Assistant) Chuẩn shadcn AI Elements

**Feature Branch**: `063-rebuild-assistant-ui`

**Created**: 2026-11-12

**Status**: Ready for Planning

**Input**: User description: "Hiện tại tôi thấy bạn code UI của http://localhost:5173/dashboard/assistant rất tệ, tôi mong muốn đập đi xây lại từ đầu bằng các ui có sẵn của shacdn kèm tài liệu shadcn AI Elements (Patterns for agentic interfaces: Chat, Message, Prompt Input, Reasoning, Tool Trace, Suggestion, Sources, Sidebar...)"

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Trải nghiệm hội thoại trực quan & mượt mà với Chat Stream (Priority: P1)

Người dùng (thành viên hoặc ban quản trị) truy cập vào trang Trợ lý AI (`/dashboard/assistant`) để trao đổi, hỏi đáp và tra cứu thông tin. Giao diện trò chuyện phải mang lại cảm giác hiện đại, chuyên nghiệp, thông thoáng và liền mạch:
- Khung cuộn hội thoại tự động bám đáy khi nội dung câu trả lời đang được sinh từng từ (streaming), nhưng không cưỡng bức cuộn nếu người dùng chủ động cuộn ngược lên để đọc lại nội dung phía trên.
- Có nút điều hướng nhanh quay về cuối tin nhắn (Scroll to Bottom) khi có nội dung mới.
- Khung nhập liệu hỗ trợ tự động mở rộng theo độ dài câu hỏi, nút gửi rõ ràng, phím tắt `Enter` gửi tin và `Shift + Enter` xuống dòng.
- Khi phản hồi đang streaming, nút gửi ở thanh PromptInput tạm thời chuyển sang trạng thái biểu tượng đang tải (Loading/Generating Spinner) và bị vô hiệu hóa; hệ thống đợi AI sinh xong toàn bộ phản hồi trước khi cho phép người dùng gửi câu hỏi tiếp theo.

**Why this priority**: Khung hội thoại là điểm tiếp xúc cốt lõi nhất của toàn bộ tính năng Trợ lý AI. Giao diện streaming mượt mà và khung nhập liệu tiện lợi quyết định 80% độ hài lòng của người dùng đối với trải nghiệm chatbot.

**Independent Test**: Người dùng truy cập trang `/dashboard/assistant`, nhập câu hỏi và quan sát câu trả lời xuất hiện từng phần với hiệu ứng bám đáy tự nhiên, không giật lag, định dạng văn bản markdown và khối mã hiển thị rõ ràng.

**Acceptance Scenarios**:

1. **Given** người dùng đang ở trang trợ lý, **When** nhập câu hỏi và bấm Gửi (hoặc nhấn Enter), **Then** câu hỏi của người dùng lập tức xuất hiện bên phải dưới dạng bong bóng tin nhắn (User Bubble), và thanh nhập liệu được làm trống.
2. **Given** trợ lý AI đang sinh phản hồi, **When** các token chữ đổ về liên tục, **Then** khung tin nhắn tự động cuộn theo luồng chữ để người dùng luôn thấy từ mới nhất.
3. **Given** trợ lý AI đang sinh phản hồi dài, **When** người dùng lăn chuột lên trên để đọc lại đoạn trước, **Then** hệ thống tạm dừng tự động cuộn và hiển thị nút "Cuộn xuống dưới" kèm chỉ báo tin nhắn mới.

---

### User Story 2 - Minh bạch hóa tư duy suy luận (Reasoning / Chain of Thought) và Gọi công cụ (Tool Execution) (Priority: P1)

Khi người dùng đặt các câu hỏi phức tạp (tra cứu điều lệ vi phạm, đối soát buổi họp, thống kê danh sách bài tập), trợ lý AI cần trải qua quá trình suy luận nội bộ (Thought) và thực thi các công cụ tra cứu hệ thống (Tool calling). 
- Toàn bộ quá trình này phải được hiển thị minh bạch, gọn gàng thông qua các khối trạng thái Trace có thể thu gọn/mở rộng:
  - Khi đang tư duy: hiển thị trạng thái "Đang suy luận..." với biểu tượng tải động.
  - Khi hoàn tất suy luận: khối tự động thu gọn lại thành "Đã suy luận" (Thought) kèm thời gian xử lý, người dùng có thể nhấp để mở rộng đọc chi tiết tư duy logic.
  - Khi gọi công cụ tra cứu dữ liệu: hiển thị rõ tên công cụ được kích hoạt (ví dụ: `Tra cứu vi phạm cá nhân`, `Khảo sát thực thể`), trạng thái thực thi (đang chạy -> thành công/thất bại) và dữ liệu tham số truy vấn dưới dạng khối mã đẹp mắt.

**Why this priority**: Tính năng này giúp người dùng tin tưởng vào câu trả lời của AI, hiểu được lý do tại sao AI đưa ra kết luận đó và kiểm chứng được AI có truy xuất đúng dữ liệu thực tế hay không.

**Independent Test**: Đặt câu hỏi đòi hỏi tra cứu công cụ (ví dụ: "Tại sao tôi bị trừ điểm tuần trước?"), quan sát khối Reasoning hiển thị dạng accordion mở rộng/thu gọn và khối Tool Trace hiển thị tiến trình gọi công cụ thành công.

**Acceptance Scenarios**:

1. **Given** AI bắt đầu bước phân tích ngữ cảnh, **When** nhận được luồng dữ liệu suy luận, **Then** giao diện hiển thị thành phần Accordion Trace "Đang suy luận..." với hiệu ứng chuyển động tinh tế.
2. **Given** AI kích hoạt công cụ tra cứu dữ liệu, **When** công cụ đang chạy, **Then** giao diện hiển thị biểu tượng bánh răng/terminal xoay kèm tên công cụ; khi chạy xong, chuyển thành tích xanh xác nhận.
3. **Given** câu trả lời hoàn tất, **When** người dùng bấm vào tiêu đề "Đã suy luận" hoặc khối công cụ, **Then** nội dung chi tiết mở ra mượt mà mà không làm nhảy vị trí trang.

---

### User Story 3 - Quản trị phiên hội thoại & Lịch sử trò chuyện chuyên nghiệp (Priority: P2)

Người dùng cần quản lý các phiên hội thoại một cách ngăn nắp và hiện đại:
- Thanh bên (Sidebar) hiển thị danh sách 5 phiên gần nhất được nhóm theo mốc thời gian rõ ràng (Hôm nay, Hôm qua, 7 ngày trước).
- Nút "Tạo cuộc trò chuyện mới" nổi bật ở đầu thanh bên.
- Cho phép người dùng chuyển đổi tức thì giữa các phiên chat đã lưu mà không bị mất dữ liệu.
- Cho phép xóa từng phiên trò chuyện thông qua hộp thoại xác nhận (Confirmation Dialog) được thiết kế đồng bộ với hệ thống giao diện, thay thế hoàn toàn các popconfirm thô sơ.
- Thanh bên (Sidebar) quản lý phiên hội thoại hỗ trợ thu gọn linh hoạt (Collapsible Sidebar với Toggle Button trên Desktop, và chuyển thành Sheet trượt vuốt tiện lợi trên Mobile) giúp tối ưu diện tích hiển thị và mở rộng tối đa không gian hội thoại.

**Why this priority**: Giúp người dùng dễ dàng tổ chức các chủ đề hỏi đáp khác nhau, mở rộng không gian làm việc trên nhiều kích thước màn hình khác nhau từ di động đến máy tính để bàn.

**Independent Test**: Người dùng tạo một phiên mới, nhắn tin, sau đó tạo tiếp phiên thứ hai, chuyển đổi qua lại giữa hai phiên và xóa thử một phiên qua hộp thoại xác nhận.

**Acceptance Scenarios**:

1. **Given** người dùng có nhiều phiên chat trong lịch sử, **When** bấm vào một phiên trong danh sách, **Then** nội dung của phiên đó được tải lại đầy đủ gồm cả tin nhắn, reasoning và tool trace.
2. **Given** người dùng muốn dọn dẹp lịch sử, **When** bấm biểu tượng xóa ở một phiên, **Then** một hộp thoại xác nhận (Dialog) xuất hiện hỏi người dùng có chắc chắn xóa; sau khi xác nhận, phiên biến mất khỏi danh sách.
3. **Given** người dùng thao tác trên màn hình nhỏ hoặc muốn mở rộng khung chat, **When** bấm nút ẩn/hiện thanh bên, **Then** thanh bên trượt đóng/mở mượt mà.

---

### User Story 4 - Gợi ý câu hỏi nhanh (Suggestions) và Nguồn trích dẫn (Sources / Citations) (Priority: P2)

Khi bắt đầu một phiên trò chuyện mới hoặc sau khi nhận được câu trả lời:
- Người dùng được hiển thị các thẻ gợi ý câu hỏi nhanh (Suggestions) phù hợp với vai trò của mình (Thành viên: "Vi phạm tháng này của tôi", "Quy chế xin nghỉ vắng"; Quản trị viên: "Tổng hợp vi phạm tuần này", "Bài tập sắp hết hạn"). Bấm vào thẻ gợi ý sẽ tự động gửi câu hỏi.
- Giao diện tập trung hoàn hảo vào các thẻ gợi ý câu hỏi nhanh (Suggestions) thích ứng theo vai trò người dùng và hiển thị định dạng khối Markdown kèm Code Block Shiki sắc nét; các trích dẫn nguồn (Sources) và thông tin mô hình (Model Info) được hiển thị tinh tế khi backend trả về dữ liệu tương ứng.

**Why this priority**: Giúp người dùng mới không bị bỡ ngỡ khi nhìn vào khung chat trống, kích hoạt nhu cầu tra cứu và gia tăng tính minh chứng cho các câu trả lời về quy chế.

**Independent Test**: Mở một phiên chat mới, thấy các thẻ gợi ý hiển thị đẹp mắt, bấm vào một thẻ và thấy câu hỏi được gửi đi ngay lập tức; khi câu trả lời có trích dẫn, thấy danh sách nguồn đính kèm phía dưới.

**Acceptance Scenarios**:

1. **Given** màn hình chào mừng của phiên mới trống tin nhắn, **When** người dùng nhìn vào giao diện, **Then** hiển thị biểu tượng trợ lý, thông điệp hướng dẫn và lưới các thẻ gợi ý nhanh (Suggestions).
2. **Given** các thẻ gợi ý hiển thị trên màn hình, **When** người dùng nhấp vào một thẻ, **Then** nội dung thẻ được gửi đi làm câu hỏi mà không cần gõ thủ công.

---

### User Story 5 - Thống nhất ngôn ngữ thiết kế thuần khiết và khả năng chuyển đổi giao diện (Priority: P3)

Giao diện Trợ lý AI phải tuân thủ nghiêm ngặt ngôn ngữ thiết kế hiện đại của hệ thống:
- Sử dụng 100% các thành phần giao diện chuẩn (shadcn/ui composition) và bộ biểu tượng Lucide đồng bộ; loại bỏ hoàn toàn các thành phần Ant Design chắp vá (Antd Button, Popconfirm, Antd Icons).
- Tương thích hoàn hảo với chế độ Sáng / Tối (Light / Dark Mode), đảm bảo độ tương phản cao, phông chữ thanh thoát, bo góc và đổ bóng tinh tế.
- Khung hiển thị mã nguồn (Code Block) hỗ trợ làm nổi bật cú pháp đẹp mắt (syntax highlighting), có nút sao chép nội dung nhanh (Copy to clipboard).

**Why this priority**: Mang lại diện mạo đồng bộ, đẳng cấp sản phẩm thương mại cho toàn bộ hệ thống, loại bỏ sự cộc lệch và cảm giác thiếu chuyên nghiệp của giao diện cũ.

**Independent Test**: Chuyển đổi giữa chế độ Sáng và Tối, kiểm tra các thành phần nút bấm, màu nền, đường viền và khối mã hiển thị rõ ràng, không có lỗi vỡ layout hoặc phông chữ sai lệch.

**Acceptance Scenarios**:

1. **Given** người dùng kích hoạt giao diện tối (Dark Mode), **When** xem khung chat, **Then** màu nền, văn bản, các khối Trace và bong bóng chat chuyển sang tông màu tối êm dịu, không chói mắt.
2. **Given** câu trả lời chứa khối mã hoặc bảng dữ liệu, **When** hiển thị trên màn hình, **Then** khối mã có thanh tiêu đề hiển thị ngôn ngữ và nút sao chép tiện lợi.

---

### Edge Cases

- **Mất kết nối mạng hoặc lỗi máy chủ khi đang nhận phản hồi**: Giao diện hiển thị thông báo lỗi rõ ràng kèm nút "Thử lại" (Retry), không để người dùng ở trạng thái tải vô hạn.
- **Văn bản câu hỏi hoặc câu trả lời cực dài**: Khung nhập liệu giới hạn độ cao tối đa (max-height) và có thanh cuộn nội bộ; bong bóng tin nhắn ngắt dòng chuẩn xác, không làm tràn bề ngang màn hình.
- **Người dùng gửi tin nhắn liên tục trong khi câu trước chưa phản hồi xong**: Nút gửi tạm thời vô hiệu hóa và hiển thị spinner xoay tròn để ngăn chặn gửi trùng lặp.
- **Dữ liệu tham số công cụ quá lớn hoặc rỗng**: Khối Tool Trace tự động định dạng gọn gàng, hỗ trợ cuộn ngang nếu nội dung chi tiết quá dài mà không phá vỡ cấu trúc khối tin nhắn.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI xây dựng lại toàn bộ giao diện trang Trợ lý AI (`/dashboard/assistant`) dựa trên cấu trúc các mẫu thiết kế agentic của shadcn AI Elements (Chat, Message, MessageScroller, PromptInput, Reasoning, Tool Trace, Suggestion).
- **FR-002**: Hệ thống PHẢI loại bỏ hoàn toàn các thư viện giao diện cũ không đồng bộ (Ant Design icons, Antd Button, Antd Popconfirm) khỏi trang Trợ lý AI, thay thế 100% bằng bộ thành phần shadcn/ui và bộ biểu tượng Lucide React.
- **FR-003**: Thành phần Chat PHẢI tích hợp bộ cuộn thông minh (MessageScroller) với các tính năng:
  - Tự động bám đáy khi đang streaming.
  - Tạm dừng cuộn khi người dùng can thiệp cuộn thủ công lên trên.
  - Hiển thị nút "Cuộn xuống đáy" có hiệu ứng mượt mà khi người dùng ở vị trí cách đáy màn hình một khoảng nhất định.
- **FR-004**: Thành phần Message PHẢI hiển thị phân định rõ ràng giữa người dùng (User) và trợ lý (Assistant):
  - Tin nhắn người dùng hiển thị dạng bong bóng nổi bật (Bubble) căn lề phải.
  - Tin nhắn trợ lý hiển thị căn lề trái với bố cục thông thoáng, hỗ trợ phân cấp hiển thị các thành phần Trace (Reasoning, Tool) phía trên nội dung văn bản chính.
- **FR-005**: Thành phần PromptInput PHẢI hỗ trợ:
  - Tự động dãn nở chiều cao theo nội dung văn bản (auto-grow textarea).
  - Phím tắt tiện lợi: `Enter` để gửi, `Shift + Enter` để xuống dòng.
  - Nút hành động gửi tin nhắn có biểu tượng trực quan, tự động chuyển sang trạng thái biểu tượng đang tải (Loading/Generating Spinner) và bị vô hiệu hóa khi AI đang sinh câu trả lời; đợi AI sinh xong toàn bộ mới cho phép gửi tiếp.
- **FR-006**: Thành phần Reasoning PHẢI được xây dựng trên nền tảng Trace Collapsible:
  - Trạng thái đang chạy: hiển thị nhãn "Thinking..." kèm hiệu ứng tải.
  - Trạng thái hoàn thành: hiển thị nhãn "Thought" kèm thời gian/mô tả thu gọn.
  - Hỗ trợ người dùng nhấp để mở rộng/thu gọn khối nội dung suy luận mà không gây gián đoạn luồng đọc.
- **FR-007**: Thành phần Tool Trace PHẢI hiển thị chi tiết các lần gọi công cụ:
  - Hiển thị tên thân thiện của công cụ đã thực thi.
  - Hiển thị trạng thái thành công hoặc cảnh báo lỗi.
  - Cho phép mở rộng xem tham số đầu vào và kết quả trả về dưới dạng khối dữ liệu có định dạng.
- **FR-008**: Thành phần Suggestion PHẢI hiển thị danh sách các gợi ý câu hỏi nhanh (Quick Prompts) thích ứng theo vai trò người dùng khi bắt đầu phiên mới:
  - Dạng danh sách thẻ/viên thuốc (pill cards) có thể bấm nhanh một chạm để gửi ngay.
  - Tự động ẩn đi khi cuộc trò chuyện đã có nhiều hơn 2 lượt trao đổi để tránh chiếm dụng diện tích màn hình.
- **FR-009**: Hệ thống PHẢI xây dựng lại thanh bên quản lý phiên trò chuyện (ChatSessionSidebar):
  - Nút "Đoạn chat mới" nổi bật.
  - Danh sách phiên hiển thị tiêu đề súc tích, đánh dấu phiên đang mở.
  - Xác nhận xóa phiên bằng Hộp thoại Xác nhận (AlertDialog/Dialog) chuẩn shadcn, loại bỏ hoàn toàn Popconfirm cũ.
  - Hỗ trợ thu gọn linh hoạt (Collapsible Sidebar) với nút toggle ẩn/hiện trên máy tính để bàn và dạng Sheet trượt trên màn hình di động.
- **FR-010**: Tất cả các khối mã nguồn (Code Blocks) trong câu trả lời markdown PHẢI được tô màu cú pháp (Syntax Highlighting) và có nút sao chép nhanh văn bản vào bộ nhớ tạm.
- **FR-011**: Phạm vi tái thiết đợt này tập trung 100% vào việc xây dựng hoàn hảo trang `/dashboard/assistant`; thành phần nút chat nổi `FloatingChatButton` toàn trang chỉ đóng vai trò nút tắt điều hướng nhanh dẫn thẳng người dùng vào `/dashboard/assistant`.

---

### Key Entities *(include if feature involves data)*

- **ChatSessionItem**: Bản ghi đại diện cho một phiên trò chuyện (ID, tiêu đề, thời điểm tạo, thời điểm cập nhật).
- **ChatMessageTurn**: Đại diện cho một lượt tin nhắn hoàn chỉnh, chứa vai trò (`user` hoặc `assistant`), nội dung hiển thị markdown, trạng thái streaming, và siêu dữ liệu đi kèm (`reasoning_content`, `tools_invoked`, `sources`).
- **ToolTraceRecord**: Đại diện cho một bước thực thi công cụ trong lượt trả lời của trợ lý (tên công cụ, trạng thái thực thi, tham số truyền vào, kết quả phản hồi).
- **SuggestionItem**: Đại diện cho một thẻ gợi ý câu hỏi tương tác (tiêu đề hiển thị, nội dung câu lệnh gửi đi, phân loại gợi ý).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% các thành phần giao diện trên trang `/dashboard/assistant` được chuyển đổi sang chuẩn shadcn/ui và shadcn AI Elements, hoàn toàn không còn sự xuất hiện của Ant Design components hay Antd icons.
- **SC-002**: Tốc độ phản hồi giao diện khi người dùng gửi câu hỏi và bắt đầu nhận luồng hiển thị (streaming) đạt dưới 300ms kể từ khi máy chủ phản hồi gói dữ liệu đầu tiên.
- **SC-003**: 100% các lượt suy luận (Reasoning) và gọi công cụ (Tool Calls) được gói gọn gàng trong các khối Trace có thể đóng/mở, không làm vỡ hoặc kéo dài vô lý chiều cao khung chat.
- **SC-004**: Trải nghiệm thao tác trên thiết bị di động và máy tính bảng đạt chuẩn phản hồi 100%, không bị tràn ngang màn hình (zero horizontal overflow) và thanh bên hoạt động mượt mà dưới dạng Sheet.
- **SC-005**: Thao tác sao chép khối mã nguồn và gửi câu hỏi gợi ý nhanh hoạt động chính xác với 1 lần nhấp chuột duy nhất.

---

## Assumptions

- Người dùng truy cập trang trợ lý là người dùng đã đăng nhập hợp lệ vào hệ sinh thái DUT AI Manager.
- Dịch vụ backend API chat và SSE streaming đã hoạt động ổn định và cung cấp đầy đủ thông tin về `reasoning_content` và `tools_invoked`.
- Hệ thống hỗ trợ sẵn Tailwind CSS và các biến màu CSS chuẩn (CSS Variables) tương thích với cả Light mode và Dark mode.
- Cấu trúc dữ liệu hội thoại không thay đổi giao thức cốt lõi, việc tái cấu trúc tập trung tối đa vào tầng trình diễn (Presentation Layer / Components) theo đúng nguyên lý Constitution VIII.
