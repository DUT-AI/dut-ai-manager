# Quickstart & Verification Guide: Tái Thiết Giao Diện Trợ Lý Ảo (AI Assistant)

**Feature Branch**: `063-rebuild-assistant-ui`  
**Date**: 2026-11-12  
**Status**: Completed  

---

## 1. Điều Kiện Tiên Quyết (Prerequisites)

1. Máy chủ Backend đang chạy:
   ```bash
   cd backend && uv run uvicorn app.main:app --port 8001 --reload
   ```
2. Máy chủ Frontend đang chạy:
   ```bash
   cd frontend && npm run dev
   ```
3. Trình duyệt truy cập tại: `http://localhost:5173/dashboard/assistant`
4. Tài khoản kiểm thử: Đăng nhập với tài khoản hợp lệ (Sinh viên hoặc Ban Quản Trị / Mentor).

---

## 2. Kịch Bản Kiểm Thử & Xác Minh Đầu-Cuối (End-to-End Validation Scenarios)

### Kịch bản 1: Kiểm thử Màn hình Chào mừng & Thẻ Gợi ý Nhanh (Suggestions)
- **Hành động**:
  1. Mở trang `http://localhost:5173/dashboard/assistant`.
  2. Quan sát màn hình khi phiên chat chưa có tin nhắn nào.
- **Kết quả kỳ vọng**:
  - Biểu tượng trợ lý (`BotIcon`) và dòng thông điệp chào mừng hiển thị căn giữa sắc nét.
  - Các thẻ gợi ý nhanh dạng viên thuốc (`QuickPrompts`) hiển thị tương ứng với vai trò tài khoản (ví dụ: "Vi phạm tháng này của tôi", "Quy chế xin nghỉ vắng").
  - Thanh nhập liệu `PromptInput` nằm ở dưới cùng với chữ gợi ý (placeholder) rõ ràng.

### Kịch bản 2: Kiểm thử Gửi Tin Nhắn & Luồng Streaming (MessageScroller & Reasoning)
- **Hành động**:
  1. Nhấp chuột vào một thẻ gợi ý (hoặc gõ câu hỏi: *"Quy định xin phép vắng họp trước mấy tiếng?"*) và nhấn Enter.
- **Kết quả kỳ vọng**:
  - Bong bóng tin nhắn người dùng (`Bubble`) xuất hiện ngay lập tức bên phải.
  - Nút gửi ở `PromptInput` chuyển sang icon xoay tải (`Loader2Icon`) và vô hiệu hóa.
  - Khối `Reasoning` xuất hiện đầu câu trả lời với trạng thái "Thinking..." xoay tròn và hiệu ứng chữ mờ chuyển động.
  - Khi nội dung phản hồi chính bắt đầu đổ về, `MessageScroller` tự động cuộn bám đáy mượt mà.
  - Khi hoàn tất, khối `Reasoning` chuyển thành icon tích tròn ("Thought") và tự thu gọn.
  - Nút gửi ở `PromptInput` tự mở khóa lại cho câu hỏi kế tiếp.

### Kịch bản 3: Kiểm thử Khối Mã Nguồn & Định Dạng Markdown
- **Hành động**:
  1. Đặt câu hỏi yêu cầu ví dụ cấu trúc dữ liệu hoặc lệnh (ví dụ: *"Cú pháp gọi API kiểm tra vi phạm"*).
- **Kết quả kỳ vọng**:
  - Khối code hiển thị bằng `<CodeBlock>` chuẩn shadcn có nền tối thanh lịch, tên ngôn ngữ (`json` hoặc `bash`) ở thanh header.
  - Nhấp nút "Copy code": Biểu tượng chuyển từ copy sang tích xanh (`CheckIcon`) và văn bản được sao chép vào bộ nhớ tạm.

### Kịch bản 4: Kiểm thử Thu Gọn Thanh Bên & Xóa Phiên Hội Thoại
- **Hành động**:
  1. Bấm nút thu gọn thanh bên (`PanelLeftCloseIcon`) trên thanh Header.
  2. Quan sát khung chat tự động mở rộng toàn màn hình.
  3. Bấm mở lại thanh bên (`PanelLeftIcon`).
  4. Rê chuột vào một phiên trò chuyện cũ, nhấp vào biểu tượng thùng rác (`Trash2Icon`).
- **Kết quả kỳ vọng**:
  - Hộp thoại shadcn `Dialog` xuất hiện hỏi: *"Xác nhận xóa phiên trò chuyện này?"*.
  - Bấm "Hủy": Hộp thoại đóng lại, phiên được giữ nguyên.
  - Bấm "Xóa": Phiên biến mất khỏi danh sách phiên gần đây, thông báo thành công hiển thị.

### Kịch bản 5: Kiểm thử Tính Tương Thích Di Động (Mobile Responsive)
- **Hành động**:
  1. Bật chế độ Responsive trên DevTools (kích thước màn hình `< 768px`).
- **Kết quả kỳ vọng**:
  - Thanh bên tự động ẩn, thanh Header xuất hiện nút menu mở thanh bên dạng Sheet trượt từ bên trái.
  - Chiều rộng khung tin nhắn tự co giãn thích ứng, không xuất hiện thanh cuộn ngang (zero horizontal overflow).

---

## 3. Lệnh Kiểm Tra Chất Lượng Mã Nguồn (Lint & Typecheck)

Chạy các lệnh kiểm thử tĩnh để đảm bảo không có lỗi type hoặc lint:
```bash
cd frontend
npm run typecheck
npm run lint
```
Kết quả yêu cầu: Không có lỗi typescript (`tsc -b`) và không có lỗi eslint.
