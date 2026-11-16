# Quickstart & Verification Guide: Unified Homework Submission Status

**Feature**: `069-unify-homework-submission-status`  
**Date**: 2026-11-15  

Tài liệu này hướng dẫn các bước kiểm thử xác thực tính năng end-to-end nhằm đảm bảo trạng thái hoàn thành bài tập thống nhất giữa Học viên và Quản lý.

---

## 1. Môi trường & Điều kiện Tiên quyết

1. Backend đang chạy trên cổng 8000 (hoặc môi trường test pytest).
2. Frontend đang chạy trên Vite dev server (`http://localhost:5173`).
3. Dữ liệu thử nghiệm:
   - Bài tập $H_1$ (ví dụ: `Gen2: Đại số tuyến tính`) yêu cầu Coding (`requires_coding=True`), có 2 bài tập con ($E_1$ và $E_2$).
   - Học sinh $S_1$ (ví dụ: User ID 12) mới chỉ hoàn thành bài $E_1$ (`is_passed=True`), chưa nộp bài $E_2$.

---

## 2. Kịch bản Kiểm thử Backend (Automated Tests)

Chạy bộ test suite của domain homework:

```bash
cd backend
pytest tests/unit/test_homework_validation.py -v
pytest tests/unit/test_get_homework_detail_use_case.py -v
pytest tests/unit/test_homework_checker.py -v
```

### Kịch bản Unit Test mới cần bổ sung:
1. `test_evaluate_submissions_with_partial_coding`:
   - Giao bài tập có 2 bài coding con: `{"ex-1", "ex-2"}`.
   - Submissions chỉ có 1 bài `ex-1` pass.
   - Kết quả: `evaluation.is_submitted == False`, `evaluation.coding_status == "PARTIALLY_SUBMITTED"`, `uncompleted_items` chứa thông tin thiếu bài coding.
2. `test_get_user_homeworks_use_case_returns_partial_status`:
   - Kiểm tra `GetUserHomeworksUseCase.execute()` trả về `is_submitted=False` và `coding_status="PARTIALLY_SUBMITTED"`.

---

## 3. Kịch bản Kiểm thử Giao diện Người dùng (E2E / Manual Verification)

### Kịch bản 1: Kiểm tra Giao diện Học viên (`/dashboard/my-homeworks`)
1. Đăng nhập với tài khoản học sinh $S_1$.
2. Điều hướng đến trang **"Bài tập của tôi"**.
3. **Quan sát Thẻ Bài tập**:
   - Thẻ bài tập $H_1$ có viền trái màu hổ phách/cam (Amber).
   - Biểu tượng trạng thái là icon đồng hồ/cảnh báo màu cam (không phải dấu tích xanh lá).
   - Tag tiến độ hiển thị: `Tiến độ: 1/2 bài con` (hoặc `Chưa hoàn thành đủ`).
4. **Quan sát Bộ lọc Tabs**:
   - Tab **"Chưa nộp"**: Thấy bài tập $H_1$ xuất hiện tại đây.
   - Tab **"Đã nộp"**: Bài tập $H_1$ **KHÔNG** xuất hiện tại đây.
   - Bộ đếm thống kê "Chưa nộp" tăng thêm 1.

### Kịch bản 2: Kiểm tra Chi tiết Bài tập Học viên (`/dashboard/my-homeworks/:id`)
1. Từ thẻ bài tập $H_1$, bấm "Xem chi tiết".
2. **Quan sát**:
   - Thanh tiến độ hiển thị `1/2 bài tập con (50% hoàn thành)`.
   - Trạng thái chung hiển thị "Chưa hoàn thành".
   - Danh sách bài con: Bài 1 "Đã nộp", Bài 2 "Chưa nộp".
   - $\rightarrow$ **Khớp 100% với thông tin hiển thị trên thẻ bên ngoài.**

### Kịch bản 3: Kiểm tra Giao diện Quản lý Bài tập (`/dashboard/homework/:id`)
1. Đăng nhập với tài khoản Admin / Leader.
2. Mở chi tiết bài tập $H_1$.
3. **Quan sát Tab Coding**:
   - Học sinh $S_1$ nằm ở cột/danh sách **"Chưa nộp / Làm dở"** với nhãn `1/2`.
   - $\rightarrow$ **Đồng bộ và thống nhất hoàn toàn với giao diện học viên.**
