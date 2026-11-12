# Feature Specification: Nâng cấp kiến trúc chatbot thành Agent Loop (ReAct / Multi-turn Tool Loop)

**Feature ID**: `064-agent-loop-architecture`  
**Trạng thái**: Draft / In Planning  
**Ngày tạo**: 2026-11-12  

---

## 1. Giới thiệu & Động lực (Context & Motivation)

Hiện tại, chatbot hỗ trợ nội bộ (`dut-ai-manager`) hoạt động theo mô hình **Single-Turn Tool Execution**:
1. Người dùng gửi câu hỏi.
2. Trợ lý gọi LLM một lần. Nếu LLM yêu cầu gọi tool (`pending_tool_calls`), hệ thống thực thi các tool này trong 1 vòng lặp cục bộ (`_execute_tools`).
3. Sau đó, hệ thống gọi LLM lần 2 với kết quả của tool và stream câu trả lời cuối cùng (`stream_chat(..., tools=None)`).

### Hạn chế nghiêm trọng của mô hình hiện tại:
- **Không hỗ trợ chuỗi suy luận đa bước (Multi-step Reasoning & Chaining)**: Ví dụ: Người dùng hỏi *"Những ai chưa nộp bài tập gần nhất và đã từng vắng mặt không phép ở buổi học gần nhất?"*. Trợ lý cần:
  - Bước 1: Tra cứu bài tập mới nhất & danh sách chưa nộp bài (`admin_get_unsubmitted_homeworks`).
  - Bước 2: Dựa vào kết quả bước 1, tiếp tục tra cứu buổi họp gần nhất & danh sách vắng (`admin_get_meeting_absentees`).
  - Bước 3: Đối soát 2 tập dữ liệu và tổng hợp trả lời.
  - Hiện tại do chỉ có 1 vòng tool call, LLM không thể gọi tiếp tool ở bước 2 nếu bước 1 cần xem kết quả trước.
- **Không có cơ chế tự sửa sai (Self-Correction / Reflection)**: Khi tool trả về kết quả rỗng hoặc báo lỗi tham số (ví dụ sai định dạng ngày, sai ID), LLM không có cơ hội thử lại với tham số đã điều chỉnh hoặc thử phương án dự phòng.
- **Dễ dẫn đến hallucination hoặc từ chối trả lời** khi câu hỏi phức tạp vượt quá khả năng xử lý trong 1 lần gọi tool.

---

## 2. Mục tiêu (Goals & Non-Goals)

### Mục tiêu chính (Goals):
1. **Nâng cấp kiến trúc luồng xử lý thành Agent Loop (ReAct / Multi-turn Iteration)**: Cho phép LLM thực hiện một vòng lặp: Suy luận (`Thought/Reasoning`) -> Hành động (`Action/Tool Call`) -> Quan sát (`Observation/Tool Result`) -> Tự đánh giá & Lặp lại cho đến khi đạt kết quả thỏa mãn hoặc chạm ngưỡng dừng (`max_iterations`).
2. **Kiểm soát an toàn & Tài nguyên (Safety Guardrails & Limits)**:
   - Giới hạn số vòng lặp tối đa (`max_iterations` = 5 mặc định).
   - Cơ chế phát hiện lặp vô hạn (Cycle/Duplicate tool call detection).
   - Quản lý context window: Cắt tỉa (prune) các kết quả tool quá dài để không làm tràn token của local model.
3. **Phát trực tuyến thời gian thực (Real-time SSE Streaming Transparency)**:
   - Người dùng trên giao diện shadcn AI Elements có thể thấy từng bước suy luận, từng tool được gọi và kết quả từng tool trong thời gian thực, không phải chờ đợi trong im lặng.
4. **Bảo tồn Clean Architecture & DDD**:
   - Tách biệt rõ ràng giữa Agent Loop Runner / Orchestrator và Tool Registry.
   - Giữ nguyên các quyền hạn RBAC và tính bảo mật của từng Tool.

### Ngoài phạm vi (Non-Goals):
- Không thay đổi backend LLM host (`https://llm2.dutai.site/v1`).
- Không sinh ra subagent độc lập chạy background bất đồng bộ vô thời hạn (ở giai đoạn này chỉ tập trung vào Agent Loop đồng bộ theo phiên chat của người dùng).
- Không can thiệp sửa đổi các quyền hạn bảo mật RBAC sẵn có của Tool.

---

## 3. Yêu cầu Người dùng & Kịch bản (User Scenarios & Requirements)

### Kịch bản 1: Tra cứu liên hoàn (Multi-step Investigation)
- **Actor**: Mentor / Trainer.
- **Hành động**: Đặt câu hỏi: *"Kiểm tra giúp anh xem bạn Nguyễn Văn A gần đây có bị vi phạm bài tập nào không, và bạn đó đã gửi đơn xin phép cho bài tập đó chưa?"*.
- **Hành vi Agent Loop**:
  - Vòng 1: Gọi `inspect_entity_records(entity_type='homework', user_id=...)` -> Nhận kết quả có bài tập quá hạn.
  - Vòng 2: Phân tích thấy có bài quá hạn, tự động gọi tiếp `inspect_entity_records(entity_type='permission_request', user_id=...)` để đối soát đơn từ.
  - Vòng 3: Tổng hợp câu trả lời hoàn chỉnh dựa trên cả 2 kết quả.

### Kịch bản 2: Tự sửa sai khi tham số tìm kiếm không khớp (Self-Correction)
- **Actor**: Thành viên CLB.
- **Hành động**: *"Tại sao tuần trước em bị phạt nộp bài tập Python?"*.
- **Hành vi Agent Loop**:
  - Vòng 1: Tìm kiếm bài tập với từ khóa "Python" -> Nếu kết quả rỗng do tên bài tập lưu là "Lập trình Python Nâng Cao Tuần 3", Agent tự động gọi tool tra cứu danh sách bài tập được giao của cá nhân để tìm đúng tên.
  - Vòng 2: Tra cứu chi tiết tiến độ nộp bài của bài tập đã tìm được.
  - Vòng 3: Giải thích rõ ràng cho thành viên.

### Kịch bản 3: Chạm ngưỡng dừng an toàn (Max Iterations Guard)
- **Hành vi**: Nếu sau `max_iterations` (ví dụ 5 vòng) mà Agent vẫn chưa ra được câu trả lời cuối cùng, hệ thống chủ động ngắt vòng lặp, gửi thông báo tóm tắt các bước đã thực hiện kèm câu trả lời tốt nhất hiện có, tránh treo hệ thống hoặc timeout SSE.
