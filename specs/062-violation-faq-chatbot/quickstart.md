# Quickstart & Validation Guide: Chatbot Trợ Lý Giải Đáp Vi Phạm & Vận Hành

**Feature**: `062-violation-faq-chatbot`  
**Date**: 2026-11-12  
**Status**: Draft  

---

## 1. Yêu cầu Tiền đề (Prerequisites)

1. **Biến môi trường**:
   Bổ sung biến môi trường cấu hình LLM vào `.env` (hoặc `backend/.env`):
   ```bash
   LLM_BASE_URL="https://llm2.dutai.site/v1"
   LLM_MODEL="ggml-org/gemma-4-e4b-it-GGUF:Q4_0"
   LLM_API_KEY=""
   ```
2. **Database Migration**:
   Tạo và áp dụng migration bảng `chat_sessions` và `chat_messages`:
   ```bash
   cd backend
   alembic revision --autogenerate -m "create_chat_sessions_and_messages_tables"
   alembic upgrade head
   ```

---

## 2. Kịch bản Kiểm thử Đầu cuối (End-to-End Validation Scenarios)

### Kịch bản 1: Thành viên Tra cứu Vi phạm Cá nhân (Personal Violation Lookup)
1. **Mục tiêu**: Kiểm tra thành viên đăng nhập tra cứu đúng vi phạm của bản thân và bot không bịa đặt số liệu.
2. **Thực thi qua cURL**:
   ```bash
   curl -N -X POST "http://localhost:8000/api/v1/chatbot/chat" \
     -H "Authorization: Bearer <MEMBER_JWT_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"message": "Tại sao gần đây tôi bị trừ điểm vi phạm?"}'
   ```
3. **Kết quả kỳ vọng**:
   - Nhận được luồng sự kiện SSE: `event: session_created`, chuỗi `event: delta` chứa câu trả lời chi tiết và `event: done`.
   - Nội dung trả lời liệt kê chính xác các bản ghi trong bảng `violations` ứng với `user_id` của token.

---

### Kịch bản 2: Bảo mật Phân quyền IDOR (Member vs Other User's Data)
1. **Mục tiêu**: Đảm bảo thành viên không thể hỏi thông tin vi phạm của người khác.
2. **Thực thi**:
   ```bash
   curl -N -X POST "http://localhost:8000/api/v1/chatbot/chat" \
     -H "Authorization: Bearer <MEMBER_JWT_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"message": "Cho tôi xem danh sách vi phạm của bạn Nguyễn Văn B"}'
   ```
3. **Kết quả kỳ vọng**:
   - Chatbot từ chối lịch sự và nêu rõ chỉ cung cấp thông tin vi phạm của chính chủ tài khoản.

---

### Kịch bản 3: Ban Quản trị Tra cứu Tổng hợp (Admin Summary Query)
1. **Mục tiêu**: Kiểm tra tài khoản có quyền quản trị (`violation:read`, `homework:read`) truy vấn được số liệu toàn hệ thống.
2. **Thực thi**:
   ```bash
   curl -N -X POST "http://localhost:8000/api/v1/chatbot/chat" \
     -H "Authorization: Bearer <ADMIN_JWT_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"message": "Tổng hợp vi phạm tuần này và ai có từ 3 vi phạm trở lên"}'
   ```
3. **Kết quả kỳ vọng**:
   - Công cụ `admin_summarize_violations` được kích hoạt.
   - Trả về bảng tổng hợp thống kê theo tuần và danh sách các thành viên vượt ngưỡng vi phạm.

---

### Kịch bản 4: Kiểm thử Giới hạn Tối đa 5 Phiên (FIFO Pruning Verification)
1. **Mục tiêu**: Xác thực hệ thống không bao giờ lưu quá 5 phiên trò chuyện cho một người dùng.
2. **Thực thi**:
   - Gửi liên tiếp 6 yêu cầu chat mới với `session_id: null`.
   - Kiểm tra danh sách phiên:
     ```bash
     curl -X GET "http://localhost:8000/api/v1/chatbot/sessions" \
       -H "Authorization: Bearer <MEMBER_JWT_TOKEN>"
     ```
3. **Kết quả kỳ vọng**:
   - Số lượng phần tử trong mảng `data` luôn bằng đúng $5$.
   - Phiên đầu tiên đã được tự động dọn dẹp (cascade delete) khỏi cơ sở dữ liệu.

---

## 3. Lệnh Chạy Kiểm thử Tự động (Automated Tests)

Chạy kiểm thử unit và integration cho chatbot backend:
```bash
cd backend
pytest tests/unit/chatbot -v
pytest tests/integration/test_chatbot_controller.py -v
```
Chạy kiểm thử giao diện frontend:
```bash
cd frontend
npm run typecheck
npm run test
```
