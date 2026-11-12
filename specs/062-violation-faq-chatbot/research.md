# Research & Technical Decisions: Chatbot Trợ Lý Giải Đáp Vi Phạm & Vận Hành

**Feature**: `062-violation-faq-chatbot`  
**Date**: 2026-11-12  
**Status**: Completed  

---

## 1. Quyết định 1: Mô hình LLM & Cơ chế Kết nối (Private LLM Endpoint)

### Quyết định
Sử dụng **mô hình tự lưu trữ nội bộ (Self-hosted on-premise)** thông qua endpoint OpenAI-compatible:
- **Base URL**: `https://llm2.dutai.site/v1`
- **Model ID**: `ggml-org/gemma-4-e4b-it-GGUF:Q4_0` (llamacpp server, context window ~66k tokens)
- **Cơ chế kết nối**: Sử dụng thư viện `openai` Async client (`AsyncOpenAI`) hoặc HTTP client bất đồng bộ (`httpx`/`aiohttp`) trỏ trực tiếp đến `https://llm2.dutai.site/v1/chat/completions` với `stream=True`.

### Lý do (Rationale)
1. **Bảo mật Dữ liệu Nội bộ & Riêng tư Tuyệt đối (Data Privacy)**: Toàn bộ dữ liệu vi phạm của thành viên, điểm danh, đơn xin phép và hoạt động học vụ của DUT được xử lý hoàn toàn trên hạ tầng máy chủ riêng của hệ thống (`dutai.site`), không gửi dữ liệu người dùng ra bất kỳ dịch vụ đám mây của bên thứ ba nào (như Google/OpenAI).
2. **Chi phí & Độ ổn định**: Không mất phí gọi token theo lượt, không phụ thuộc vào hạn ngạch (rate limits) của các nhà cung cấp bên ngoài.
3. **Chuẩn OpenAI Compatible**: Cho phép sử dụng các SDK chuẩn (`AsyncOpenAI` hoặc `aiohttp`), dễ dàng cấu hình qua biến môi trường `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`.
4. **Hỗ trợ Context Window lớn**: Model có context size lên tới ~66k tokens (`n_ctx: 66816`), thoải mái nạp toàn bộ tài liệu quy chế tổ chức và ngữ cảnh vi phạm của người dùng.

### Các phương án khác đã xem xét
- **Agent Harness (LangGraph / CrewAI / AutoGen)**: Bị bác bỏ vì gây độ trễ rất lớn (> 10-15s cho mỗi câu hỏi), tốn kém token, khó viết kiểm thử độc lập và vi phạm nguyên tắc Clean Architecture của dự án.
- **RAG thuần túy không có Tool Calling**: Bị bác bỏ vì RAG chỉ tra cứu được văn bản tĩnh (quy chế), không thể truy vấn dữ liệu động theo thời gian thực của từng thành viên (như lịch sử vi phạm, deadline bài tập cá nhân).

---

## 2. Quyết định 2: Giao thức Truyền Dữ liệu Luồng (SSE vs WebSocket)

### Quyết định
Sử dụng **Server-Sent Events (SSE)** thông qua endpoint HTTP `POST /api/v1/chatbot/chat` trả về `StreamingResponse(media_type="text/event-stream")`.

### Lý do (Rationale)
1. **Phù hợp bản chất đối thoại 1 chiều**: Người dùng gửi 1 câu hỏi -> Hệ thống stream câu trả lời về liên tục. SSE là giao thức chuẩn trên nền HTTP/1.1 và HTTP/2, không cần duy trì kết nối hai chiều stateful như WebSocket.
2. **Xác thực JWT an toàn**: Yêu cầu chat gửi qua HTTP POST tiêu chuẩn kèm header `Authorization: Bearer <token>`, tận dụng 100% middleware xác thực hiện có của backend.
3. **Thân thiện với hạ tầng Proxy**: SSE tương thích mượt mà với Nginx, Docker Compose và Cloudflare mà không cần cấu hình nâng cấp socket (`Upgrade: websocket`) phức tạp.
4. **Frontend dễ tích hợp**: Sử dụng `fetch` API với `ReadableStreamDefaultReader` trên client React để đọc từng chunk và render mượt mà bằng `react-markdown`.

### Các phương án khác đã xem xét
- **WebSocket**: Quá cồng kềnh cho bài toán Q&A dạng hỏi-đáp; cần quản lý heartbeat, reconnect, auth handshake và trạng thái kết nối trên server.
- **REST Non-streaming (JSON thông thường)**: Trải nghiệm người dùng kém vì phải chờ toàn bộ câu trả lời hoàn thành (3-5 giây) mới hiển thị được dữ liệu.

---

## 3. Quyết định 3: Lưu trữ Phiên Hội Thoại & Cơ chế Giới hạn Tối đa 5 Phiên (FIFO Pruning)

### Quyết định
Lưu trữ trên cơ sở dữ liệu quan hệ **PostgreSQL** (SQLAlchemy Async ORM) với 2 bảng:
- `chat_sessions`: Đại diện cho phiên trò chuyện của người dùng (`id`, `user_id`, `title`, `created_at`, `updated_at`).
- `chat_messages`: Bản ghi tin nhắn (`id`, `session_id`, `role`, `content`, `metadata_json`, `created_at`).

Áp dụng quy tắc miền (Domain Rule) trong Use Case `CreateOrGetChatSessionUseCase`:
- Khi người dùng tạo một phiên mới: Nếu tổng số phiên của người dùng đạt ngưỡng **5 phiên**, hệ thống tự động tìm và xóa phiên cũ nhất (dựa trên `updated_at` tăng dần) kèm các tin nhắn liên quan (cascade delete).

### Lý do (Rationale)
1. **Đúng yêu cầu nghiệp vụ**: Đảm bảo thành viên xem lại được lịch sử hỏi đáp trên nhiều thiết bị nhưng không làm phình to dữ liệu.
2. **Kiểm soát dung lượng**: Giới hạn cố định $O(5 \times N_{users})$ bản ghi phiên, bảo đảm database luôn gọn gàng và truy vấn nhanh.
3. **Clean DDD**: Quy tắc 5 phiên được kiểm soát tập trung trong tầng Application / Domain, không phụ thuộc vào cron job dọn dẹp bên ngoài.

### Các phương án khác đã xem xét
- **Lưu trữ trên LocalStorage của trình duyệt**: Không đồng bộ giữa máy tính và điện thoại; người dùng xóa cache là mất hết.
- **Lưu trữ không giới hạn**: Làm tăng kích thước database không cần thiết với các đoạn chat thử nghiệm cũ.

---

## 4. Quyết định 4: Cơ chế Phân Quyền Công Cụ An Toàn (Role-Adaptive Tool Registry)

### Quyết định
Xây dựng một `ChatbotToolRegistry` được tiêm qua Dishka DI, phân giải danh sách công cụ được phép sử dụng dựa trên `current_user` và quyền hạn (`permissions`) của phiên làm việc:
- **Nhóm công cụ Cơ bản (Mọi thành viên đăng nhập)**:
  - `get_my_violations`: Tra cứu vi phạm của chính `current_user.id` (khóa cứng ID, không cho phép truyền user ID khác).
  - `get_violation_policies`: Tra cứu quy chế điểm danh, nộp bài, thời hạn xin phép.
  - `get_my_pending_tasks`: Tra cứu bài tập chưa nộp của chính mình.
- **Nhóm công cụ Quản trị Cấp cao (Chỉ kích hoạt khi có quyền `violation:read`, `homework:read`, hoặc `meeting:read`)**:
  - `admin_summarize_violations`: Báo cáo vi phạm toàn hệ thống theo tuần/tháng, top vi phạm.
  - `admin_get_unsubmitted_homeworks`: Lấy danh sách thành viên chưa nộp bài tập theo `homework_id` hoặc bài tập mới nhất.
  - `admin_get_meeting_absentees`: Danh sách vắng mặt không phép của buổi họp gần nhất.

### Lý do (Rationale)
1. **Phòng chống IDOR tuyệt đối (Zero Trust)**: Thành viên thông thường không thể ép LLM gọi công cụ quản trị vì định nghĩa công cụ đó hoàn toàn không được gửi tới LLM.
2. **Xác thực 2 lớp (Defense in Depth)**: Kể cả khi có lỗi prompt injection khiến LLM sinh ra lệnh gọi công cụ quản trị, hàm thực thi của công cụ phía backend vẫn kiểm tra lại quyền hạn của `current_user` trước khi truy vấn database.
3. **Dễ mở rộng**: Khi cần thêm công cụ cho các domain khác (`duty`, `bonus_point`), chỉ cần đăng ký thêm use case vào registry.

---

## 5. Quyết định 5: Cơ sở Tri thức Quy chế (Knowledge Base)

### Quyết định
Lưu trữ quy chế nội bộ dưới dạng file Markdown chuẩn hóa (`violation_policies.md`) được tải vào bộ nhớ hoặc inject trực tiếp vào System Prompt của LLM với cấu trúc rõ ràng (Điều 1: Điểm danh & Trễ giờ; Điều 2: Bài tập & Deadline; Điều 3: Thủ tục xin phép).

### Lý do (Rationale)
1. Nội quy phòng lab/CLB thường cô đọng (dưới 5.000 từ), hoàn toàn nằm gọn trong context window lớn của các LLM hiện đại (Gemini hỗ trợ tới 1M+ tokens).
2. Tránh việc phải duy trì thêm hạ tầng Vector Database (như pgvector/Pinecone/Milvus), giảm thiểu chi phí và sự phức tạp khi triển khai Docker.
3. Dễ dàng cập nhật: Ban quản trị chỉ cần sửa file văn bản quy chế mà không cần chạy lại pipeline re-indexing phức tạp.
