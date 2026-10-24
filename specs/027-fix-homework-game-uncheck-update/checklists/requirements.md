# Requirements Checklist: 027-fix-homework-game-uncheck-update

## 1. Specification Completeness Check
- [x] Đã làm rõ vấn đề cốt lõi (Root cause: `HomeworkRepository.update` bỏ quên cập nhật `requires_coding` và `requires_game`).
- [x] Đã mô tả rõ hành vi Frontend và Backend.
- [x] Có User Scenarios kèm Acceptance Criteria rõ ràng cho P1 và P2.
- [x] Xác định các trường hợp ngoại lệ (Edge cases): tắt game khi quiz không có game, bỏ chọn cả hai.
- [x] Tiêu chuẩn đánh giá đo lường được (Success criteria).

## 2. Requirements Validation Check
- [x] **FR-001**: `HomeworkRepository.update` cập nhật `requires_coding` và `requires_game` vào model.
- [x] **FR-002**: `UpdateHomeworkUseCase` hỗ trợ chính xác cập nhật boolean `False`.
- [x] **FR-003**: Kiểm tra validation ít nhất 1 yêu cầu được chọn.
- [x] **FR-004**: Frontend gửi chính xác payload.
- [x] **FR-005**: Kiểm thử unit test và integration test.
