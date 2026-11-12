# Quickstart & Validation Guide: Chatbot Agent DDD Refactor

**Feature Branch**: `067-agent-ddd-refactor`
**Date**: 2026-11-12

---

## 1. Mục tiêu kiểm thử & Xác thực

Xác nhận việc tái cấu trúc `Agent` theo DDD:
- `SendChatMessageUseCase` chỉ còn điều phối, không chứa logic vòng lặp hay system prompt.
- `Agent` domain service hoạt động trơn tru trong việc gọi LLM, kiểm tra chống lặp công cụ, và nén ngữ cảnh.
- 100% các unit test backend pass.
- Frontend build không lỗi.

---

## 2. Các bước xác thực (Verification Commands)

### Bước 1: Kiểm tra Unit Tests Backend
Chạy bộ kiểm thử đơn vị hiện có của chatbot:
```bash
cd backend
poetry run pytest tests/unit/test_chatbot.py tests/unit/test_database_tools.py -v
```
**Kỳ vọng**: 16/16 bài kiểm thử chạy thành công (`16 passed`).

### Bước 2: Kiểm tra Unit Tests cho Domain Service `Agent`
Viết và chạy kiểm thử độc lập cho `Agent` domain service:
- Kiểm tra `Agent.run_stream` phát ra các event `iteration_step`, `reasoning`, `tool_call_start`, `tool_call_end`, `content`, `complete`.
- Kiểm tra tính năng chống gọi trùng lặp công cụ trong `Agent`.
- Kiểm tra chính sách nén context token trong `Agent`.

### Bước 3: Kiểm tra Build Frontend
Đảm bảo mã nguồn frontend không bị ảnh hưởng và biên dịch thành công:
```bash
cd frontend
npm run build
```
**Kỳ vọng**: Lệnh `npm run build` kết thúc với mã thoát 0.
