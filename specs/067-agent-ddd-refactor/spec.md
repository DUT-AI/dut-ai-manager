# Feature Specification: Chatbot Agent DDD Refactor

**Feature Branch**: `067-agent-ddd-refactor`

**Created**: 2026-11-12

**Status**: Draft

**Input**: User description: "Tôi muốn refactor lại phần agent này theo hướng DDD, hiện tại toàn bộ logic đã code hết use case, use case chỉ là điều phối thôi"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tách biệt nhiệm vụ điều phối của Use Case và logic vòng lặp Agent (Priority: P1)

Với tư cách là một nhà phát triển hệ thống và bảo trì phần mềm, tôi muốn Use Case gửi tin nhắn chỉ đóng vai trò là một Orchestrator mỏng (điều phối session, lưu lịch sử, kích hoạt chu trình reasoning, và streaming response), trong khi toàn bộ quy tắc nghiệp vụ về vòng lặp reasoning (Agent Loop), xử lý ngữ cảnh và chính sách cắt tỉa token được đóng gói vào tầng Domain theo chuẩn Clean Architecture & DDD.

**Why this priority**: Hiện tại `SendChatMessageUseCase` đang đảm nhận quá nhiều trách nhiệm (Prompt template, token counting, context window pruning, tool invocation formatting, loop state transition, stream parsing). Điều này vi phạm nghiêm trọng Nguyên tắc I (Clean Architecture), Nguyên tắc VII (Single Responsibility Use Case), và Nguyên tắc IX (Composition & Domain Services Over Monolithic Classes) trong Constitution dự án.

**Independent Test**: Có thể kiểm thử độc lập bằng cách gửi một câu hỏi thông thường hoặc câu hỏi cần gọi công cụ. Kiểm tra use case chỉ điều phối luồng từ repository sang domain service và trả về SSE stream đầy đủ, không thay đổi bất kỳ hành vi tương tác nào đối với người dùng cuối.

**Acceptance Scenarios**:

1. **Given** một người dùng gửi câu hỏi mới đến chatbot, **When** use case tiếp nhận yêu cầu, **Then** use case xác định hoặc tạo phiên hội thoại, lưu tin nhắn của người dùng, và chuyển giao ngữ cảnh hội thoại cho Domain Service thực hiện chu trình reasoning.
2. **Given** chu trình reasoning của Agent đang chạy qua Domain Service, **When** Agent tạo ra các suy luận, gọi công cụ hoặc sinh văn bản phản hồi, **Then** các sự kiện này được phát luồng trực tiếp về Use Case để truyền tải đến giao diện người dùng mà không bị ngắt quãng.
3. **Given** chu trình reasoning kết thúc, **When** Domain Service trả về kết quả tổng hợp (nội dung, suy luận, danh sách công cụ đã gọi, token usage, timings), **Then** Use Case lưu trữ tin nhắn phản hồi của trợ lý vào cơ sở dữ liệu và hoàn tất phiên giao dịch.

---

### User Story 2 - Đóng gói chính sách quản lý ngữ cảnh và cắt tỉa Token trong Domain (Priority: P2)

Với tư cách là quản trị viên hệ thống, tôi muốn chính sách cắt tỉa ngữ cảnh (Context Pruning Policy) và chuẩn bị thông điệp đầu vào cho mô hình ngôn ngữ lớn được quản lý độc lập như một Domain Policy / Service, giúp đảm bảo mô hình không bị quá tải bộ nhớ và dễ dàng tùy biến hoặc kiểm thử độc lập mà không can thiệp vào Use Case.

**Why this priority**: Logic cắt tỉa token khi vượt ngưỡng và rút gọn kết quả công cụ cũ là một quy tắc nghiệp vụ quan trọng nhằm duy trì độ ổn định của hệ thống. Tách biệt quy tắc này giúp các kịch bản kiểm thử đơn vị có thể xác minh thuật toán nén context một cách cô lập.

**Independent Test**: Kiểm thử đơn vị cho thành phần Context Policy với danh sách thông điệp giả lập vượt ngưỡng 50,000 token, xác nhận rằng chỉ các kết quả công cụ cũ vượt độ dài cho phép mới bị nén lại, trong khi tin nhắn của người dùng và hệ thống được bảo toàn nguyên vẹn.

**Acceptance Scenarios**:

1. **Given** lịch sử hội thoại có tổng số token thấp hơn ngưỡng an toàn, **When** chính sách kiểm tra ngữ cảnh được thực thi, **Then** ngữ cảnh hội thoại được giữ nguyên vẹn không bị rút gọn.
2. **Given** lịch sử hội thoại có tổng số token vượt quá ngưỡng an toàn, **When** chính sách cắt tỉa được kích hoạt, **Then** các thông điệp công cụ cũ được nén lại có định dạng tóm tắt chuẩn xác cho đến khi dung lượng token trở về mức an toàn.

---

### User Story 3 - Bảo toàn tính toàn vẹn và tính tương thích ngược của Chatbot API & UI (Priority: P3)

Với tư cách là người dùng cuối và quản trị viên CLB sử dụng chatbot trên web, tôi muốn trải nghiệm trò chuyện, hiển thị suy luận (thinking/reasoning), hiển thị tiến trình gọi công cụ (tool trace), và tự động tra cứu cơ sở dữ liệu hoạt động chính xác 100% như trước khi refactor.

**Why this priority**: Việc refactor cấu trúc mã nguồn nội bộ phải đảm bảo nguyên tắc Zero Regression (không làm hỏng mã cũ hoặc thay đổi hợp đồng giao tiếp với frontend).

**Independent Test**: Chạy toàn bộ bộ test tự động của chatbot (`test_chatbot.py` và `test_database_tools.py`) và kiểm tra luồng build frontend, đảm bảo tất cả các kịch bản đa bước (multi-turn tool chaining), chống gọi trùng lặp (duplicate tool call prevention) và tra cứu database đều thành công.

**Acceptance Scenarios**:

1. **Given** người dùng yêu cầu tra cứu vi phạm hoặc quy chế, **When** hệ thống xử lý qua kiến trúc mới, **Then** giao diện người dùng nhận được đầy đủ các gói SSE: `iteration_step`, `tool_call_start`, `tool_call_end`, `reasoning`, `content`, `done`.
2. **Given** chu kỳ hội thoại hoàn tất, **When** người dùng tải lại lịch sử phiên trò chuyện, **Then** toàn bộ metadata (công cụ đã gọi, token usage, timings) được hiển thị đầy đủ và chính xác.

---

### Edge Cases

- Xử lý khi Domain Service gặp lỗi mạng hoặc ngắt kết nối bất thường từ phía mô hình: Use Case phải bắt được ngoại lệ miền, ghi nhận trạng thái lỗi và thông báo an toàn đến người dùng qua luồng SSE.
- Xử lý khi chu trình reasoning vượt quá số vòng lặp tối đa mà chưa ra câu trả lời cuối cùng: Domain Service phải có cơ chế fallback yêu cầu mô hình tổng hợp thông tin đã thu thập được để phản hồi người dùng.
- Xử lý trường hợp mô hình cố tình gọi lại công cụ với cùng tham số nhiều lần: Domain Service phải phát hiện chữ ký trùng lặp và bỏ qua bước thực thi dư thừa nhằm tiết kiệm tài nguyên.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI tách biệt trách nhiệm giữa Use Case (`SendChatMessageUseCase`) và logic vòng lặp suy luận của Agent, trong đó Use Case chỉ chịu trách nhiệm điều phối I/O, phiên hội thoại, lưu vết lịch sử và phân phối sự kiện SSE.
- **FR-002**: Hệ thống PHẢI đóng gói toàn bộ quy trình vòng lặp ReAct / Multi-turn Tool Chaining vào một Domain Service `Agent` thuộc tầng `domain/`.
- **FR-003**: Hệ thống PHẢI đóng gói chính sách cắt tỉa ngữ cảnh (Context Pruning Policy) và chuẩn bị prompt nghiệp vụ thành các Value Objects / Domain Policies độc lập trong tầng `domain/`.
- **FR-004**: `Agent` PHẢI quản lý trạng thái của vòng lặp (`AgentLoopState`), chữ ký cuộc gọi công cụ, và phát hiện các lệnh gọi công cụ trùng lặp trong cùng một chu trình.
- **FR-005**: Use Case PHẢI đăng ký và phân giải các phụ thuộc miền thông qua cơ chế Dependency Injection (Dishka) theo đúng Nguyên tắc II của Constitution.
- **FR-006**: Toàn bộ định dạng sự kiện SSE (`session_created`, `iteration_step`, `tool_call_start`, `tool_call_end`, `reasoning`, `content`, `done`) PHẢI được bảo toàn nguyên vẹn về cấu trúc dữ liệu để giao diện người dùng hoạt động bình thường.
- **FR-007**: Tin nhắn phản hồi của trợ lý PHẢI lưu trữ đầy đủ `ChatMessageMetadata` bao gồm `model_name`, `reasoning_content`, `tools_invoked`, `usage` và `timings` vào cơ sở dữ liệu.

### Key Entities & Domain Concepts

- **ChatSession (Domain Aggregate Root)**: Quản lý vòng đời phiên hội thoại, tự động cập nhật tiêu đề từ tin nhắn đầu tiên, và sở hữu tập hợp các `ChatMessage`.
- **ChatMessage (Domain Entity)**: Đại diện cho một tin nhắn cụ thể trong phiên, bao gồm vai trò (`USER`, `ASSISTANT`, `SYSTEM`), nội dung và `ChatMessageMetadata`.
- **AgentLoopState (Domain Value Object)**: Lưu vết số vòng lặp hiện tại, các công cụ đã thực thi, chữ ký gọi công cụ chống trùng lặp, và trạng thái hoàn tất.
- **Agent (Domain Service)**: Thực thi chu trình suy luận của Agent, tương tác với LLM Client adapter và Tool Registry để hoàn thành yêu cầu người dùng.
- **ContextPruningPolicy (Domain Policy)**: Định nghĩa quy tắc nén và cắt tỉa thông điệp công cụ lịch sử khi tổng token vượt ngưỡng an toàn.
- **AssistantPromptPolicy (Domain Value Object / Policy)**: Đóng gói các chỉ thị nghiệp vụ, nguyên tắc chống bịa đặt (Anti-Hallucination) và hướng dẫn tự sửa lỗi SQL của DUT AI Assistant.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Độ phức tạp của `SendChatMessageUseCase` giảm tối thiểu 50% số dòng code (từ ~245 dòng xuống dưới 120 dòng), chuyển toàn bộ logic thuật toán vòng lặp sang tầng Domain.
- **SC-002**: 100% các bài kiểm thử đơn vị của Chatbot (`test_chatbot.py`, `test_database_tools.py`) vượt qua mà không cần sửa đổi hành vi kiểm thử cốt lõi.
- **SC-003**: 0% hồi quy đối với giao diện người dùng Frontend: Không có thay đổi hợp đồng API, bản build `npm run build` hoàn thành không lỗi.
- **SC-004**: Mọi sự kiện suy luận và gọi công cụ vẫn được phát luồng (stream) theo thời gian thực đến người dùng với độ trễ phản hồi không đổi.

## Assumptions

- Mã nguồn tiếp tục sử dụng hệ thống Dependency Injection của Dishka (`backend/app/chatbot/providers.py`).
- Logic thực thi công cụ trong `ChatbotToolRegistry` thuộc tầng Infrastructure và tiếp tục được truyền vào Domain Service để thực thi các tool an toàn.
- Hợp đồng SSE hiện tại giữa backend và frontend là bất biến, không yêu cầu thay đổi giao diện phía React.
- Cấu hình ngưỡng token (`CHATBOT_PRUNE_TOKEN_THRESHOLD`) và số vòng lặp tối đa (`CHATBOT_MAX_ITERATIONS`) được cung cấp từ cấu hình hệ thống.
