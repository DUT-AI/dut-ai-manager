# Nghiên cứu Kiến trúc Agent Loop cho Hệ thống DUT AI Manager

**Feature ID**: `064-agent-loop-architecture`  
**Ngày nghiên cứu**: 2026-11-12  
**Tác giả**: Antigravity Orchestrator  

---

## 1. Bối cảnh & Hiện trạng Hệ thống (Current Architecture Assessment)

### Hạ tầng kỹ thuật:
- **LLM Endpoint**: On-premise OpenAI-compatible endpoint (`https://llm2.dutai.site/v1`).
- **Mô hình**: `ggml-org/gemma-4-e4b-it-GGUF:Q4_0` (mô hình 4B lượng tử hóa, tài nguyên context window có giới hạn, tối ưu cho phản hồi nhanh).
- **Backend**: Python 3.12, FastAPI, Dishka DI, SQLAlchemy ORM, clean architecture/DDD (`app/chatbot/`).
- **Frontend**: React 19, Tailwind v4, shadcn/ui AI Elements (hỗ trợ `Reasoning` trace, `ToolTrace`, `MessageScroller`).
- **Giao thức truyền thông**: Server-Sent Events (SSE) theo chuẩn OpenAI streaming chunks (`reasoning`, `content`, `tool_calls_complete`).

### Vấn đề của cơ chế hiện tại trong `SendChatMessageUseCase`:
```text
User Msg -> LLM Call 1 (tools attached) -> Tool execution (Single-pass) -> LLM Call 2 (no tools) -> Output
```
- **Không hỗ trợ multi-step tool calls**: Sau khi LLM nhận kết quả tool ở Call 2, tham số `tools=None` bị ép buộc, khiến LLM không thể gọi thêm tool nếu phát hiện cần thêm dữ liệu.
- **Không có vòng lặp trạng thái (Stateful Feedback Loop)**: Không thể lặp lại để đối soát giữa 2 tập dữ liệu (ví dụ: tìm bài tập -> lấy danh sách vắng -> đối chiếu điểm danh).

---

## 2. So sánh Các Kiến Trúc Agent Loop Phổ Biến

Dưới đây là phân tích chi tiết 4 mô hình Agent Loop trong kỹ thuật AI hiện đại:

| Tiêu chí | 1. ReAct Loop (Reasoning + Acting) | 2. Plan-and-Execute (Planner + Actor) | 3. LangGraph / StateGraph State Machine | 4. AutoGen / Multi-Agent Swarm |
| :--- | :--- | :--- | :--- | :--- |
| **Cơ chế hoạt động** | Vòng lặp đơn nhất: `Thought` -> `Action (Tool)` -> `Observation` -> lặp lại đến khi có `Final Answer`. | Pha 1: LLM lập danh sách kế hoạch các bước. Pha 2: Thực thi tuần tự từng bước qua tool. Pha 3: Tổng hợp. | Định nghĩa đồ thị trạng thái với các Node (LLM, Tool, Evaluator) và Edge có điều kiện rẽ nhánh. | Nhiều agent chuyên biệt (Router, MeetingAgent, HomeworkAgent) gửi thông điệp trao đổi qua lại. |
| **Độ phức tạp cài đặt** | **Thấp - Trung bình**: Code gọn, thuần Python async generator, không phụ thuộc framework ngoài. | **Trung bình**: Cần 2 prompt riêng (Planner prompt và Execution prompt). | **Cao**: Thêm dependency lớn (`langgraph`), học cách cấu hình state graph. | **Rất cao**: Cần quản lý hội thoại đa bên, dễ trễ và tốn token lớn. |
| **Phù hợp với model 4B (Gemma-4B)** | **Rất cao**: Prompt tinh gọn, tool calling native, không gây quá tải context cho mô hình nhỏ. | **Thấp - Trung bình**: Model 4B lập kế hoạch dài dễ bị hallucination hoặc lệch bước. | **Trung bình**: Phức tạp, dễ làm chậm thời gian phản hồi. | **Rất thấp**: Quá nặng, chi phí tính toán và latency vượt ngưỡng cho phép của mô hình nhỏ. |
| **Khả năng SSE Streaming** | **Tự nhiên**: Mỗi bước Thought / Tool call được stream trực tiếp về client realtime. | **Gián đoạn**: Phải đợi Plan xong mới bắt đầu stream hành động. | **Tốt nhưng phức tạp**: Cần map qua streaming callback của graph. | **Rất khó**: Stream phân tán từ nhiều agent con gây gián đoạn UI. |
| **Khả năng kiểm soát Guardrails** | **Cực tốt**: Giới hạn cứng `max_iterations`, ngắt vòng lặp ngay khi phát hiện lặp tool trùng lặp. | **Tốt**: Theo dõi số step trong plan. | **Tốt**: Qua đồ thị hữu hạn. | **Khó kiểm soát**: Dễ tạo vòng lặp vô tận giữa các agent. |

---

## 3. Kiến Trúc Khuyến Nghị Cho Hệ Thống: **Enhanced ReAct Loop (Autonomous Tool Loop with Guardrails)**

Đối với hệ thống `dut-ai-manager`, mô hình phù hợp và tối ưu nhất là **Enhanced ReAct Loop**:

### Sơ đồ Luồng Hoạt Động (Flowchart):

```mermaid
flowchart TD
    Start([Người dùng gửi tin nhắn]) --> Init[Khởi tạo Agent Context & History]
    Init --> LoopCheck{Vòng lặp i < max_iterations?}
    
    LoopCheck -- Có --> CallLLM[Gọi LLM stream_chat kèm Tools]
    CallLLM --> StreamThought[Stream Reasoning & Text ra SSE]
    StreamThought --> HasTools{LLM có yêu cầu Tool Call?}
    
    HasTools -- Không (Hoàn thành) --> FinalAnswer[Lưu tin nhắn & Gửi [DONE]]
    FinalAnswer --> End([Kết thúc])
    
    HasTools -- Có --> DetectLoop{Tool Call có bị lặp vô tận không?}
    DetectLoop -- Bị lặp / Trùng lặp --> InjectWarning[Chèn nhắc nhở vào context: Tool đã gọi rồi, hãy tổng hợp câu trả lời]
    InjectWarning --> NextIter[Tăng i = i + 1]
    
    DetectLoop -- Hợp lệ --> ExecTools[Thực thi Tools an toàn theo RBAC]
    ExecTools --> YieldToolTrace[Stream ToolTrace ra SSE cho UI]
    YieldToolTrace --> AppendHistory[Đính kèm kết quả Tool vào Messages Context]
    AppendHistory --> NextIter
    NextIter --> LoopCheck
    
    LoopCheck -- Không (Chạm ngưỡng Max) --> FallbackSummary[Yêu cầu LLM tổng hợp câu trả lời tốt nhất hiện có]
    FallbackSummary --> FinalAnswer
```

### Các Trụ Cột Cốt Lõi của Kiến Trúc này:

1. **Vòng lặp tự động đa bước (Multi-turn Tool Chaining)**:
   - Thay vì ngắt `tools=None` ở vòng 2, hệ thống duy trì `tools=available_tools` trong suốt vòng lặp.
   - LLM có thể gọi Tool A -> đọc kết quả -> quyết định gọi tiếp Tool B -> đọc kết quả -> sinh câu trả lời.
2. **Cơ chế Phát hiện Lặp Vô Tận (Loop & Duplicate Detection Guard)**:
   - Lưu trữ dấu vân tay `(tool_name, arguments_hash)` trong phiên chạy.
   - Nếu LLM cố tình gọi lại cùng 1 tool với cùng tham số đã thực thi trước đó, hệ thống chặn thực thi lại và phản hồi: *"Dữ liệu này đã được truy vấn ở trên, vui lòng sử dụng kết quả đã có để trả lời."*
3. **Cắt tỉa Context Thông Minh theo Ngưỡng Thực Tế (High-Capacity Context Window Guard - ~66,816 Tokens)**:
   - Mô hình/endpoint hiện tại của hệ thống hỗ trợ cửa sổ ngữ cảnh rất lớn (**~66,816 tokens**). Do đó, hệ thống **KHÔNG cắt tỉa tùy tiện** ở các vòng lặp sớm (vòng 2, vòng 3) để giữ trọn vẹn 100% độ chính xác của mọi bảng biểu dữ liệu chi tiết.
   - **Chỉ kích hoạt Context Pruning khi thực sự có nguy cơ chạm ngưỡng tràn context** (ví dụ: tổng dung lượng chuỗi messages vượt ngưỡng an toàn ~50,000 tokens hoặc ~200,000 ký tự). Lúc này mới tiến hành nén hoặc tóm tắt các kết quả tool cũ nhất ở các vòng đầu tiên.
4. **Giới Hạn Ngưỡng Dừng Cứng (Safety Guardrail)**:
   - `MAX_ITERATIONS = 5` (đủ cho 99% các câu hỏi đối soát phức tạp, không bao giờ để vòng lặp chạy quá 5 lần).
   - `TIMEOUT = 45s` cho toàn bộ vòng đời SSE.
5. **Đồng bộ Realtime với shadcn AI Elements**:
   - Stream các sự kiện `tool_started`, `tool_result` qua SSE để frontend cập nhật component `<ToolTrace />` theo từng bước sống động.

---

## 4. Quyết Định Thiết Kế Kỹ Thuật (Design Decisions)

1. **Không dùng thư viện nặng (No LangChain / LangGraph)**:
   - Cài đặt thuần túy bằng Async Generator trong Python (`AgentLoopRunner` hoặc `AgentOrchestrator`).
   - Đảm bảo tuân thủ **Clean Architecture**: Use Case điều phối qua Service, độc lập với framework ngoài, dễ viết Unit Test độc lập với mock session.
2. **Bảo tồn RBAC & Permission Security**:
   - Mọi tool call trong bất kỳ vòng lặp nào đều phải đi qua `ChatbotToolRegistry.execute_tool(..., user)` để kiểm tra quyền hạn `user.permissions`.
3. **Tương thích ngược 100% với Frontend**:
   - Giao thức SSE giữ nguyên cấu trúc JSON (`reasoning`, `content`, `done`), bổ sung thêm `tool_call` delta để UI shadcn AI Elements hiển thị bước chạy mượt mà.
