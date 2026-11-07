# Quickstart & Verification Guide: Chuẩn hóa nghiêm ngặt tiến độ bài tập con và tách biệt Game Quiz

**Feature**: `053-strict-homework-exercise-progress`  
**Date**: 2026-11-08

---

## 1. Kiểm tra tự động (Automated Verification)

### 1.1. Backend Unit Tests
Chạy pytest cho domain và use case Homework:
```bash
cd backend
pytest tests/unit/homework/ -v
```
Kiểm tra use case `GetHomeworkDetailUseCase` đảm bảo trả về đầy đủ `coding_exercises`.

### 1.2. Frontend Unit Tests / Type Checking
Kiểm tra TypeScript và các hàm helper:
```bash
cd frontend
npm run type-check # hoặc npm run build
```

---

## 2. Kiểm tra thủ công trên Giao diện (Manual E2E Scenarios)

### Kịch bản 1: Học viên Đỗ Quảng Giác xem bài tập của bản thân (`MyHomeworkDetailPage`)
1. Đăng nhập với tài khoản học viên Đỗ Quảng Giác (`user_id = 59`).
2. Truy cập: `/dashboard/my-homeworks/79` (*Gen2: Đại số tuyến tính*).
3. **Kết quả mong đợi tại Tab "Bài tập Coding"**:
   - Thấy thanh tiến độ: **"Tiến độ các bài tập con (1/2)"** (50% hoàn thành).
   - Thấy 2 tab/pill bài con:
     1. *"Bài tập đại số tuyến tính hơi cơ bản"*: Trạng thái **Đã xong** (4.5/10 - 1 lần nộp).
     2. *"Bài tập đại số tuyến tính"*: Trạng thái **Chưa nộp** (0 lần nộp, kèm nút link làm bài).
   - Tuyệt đối **không hiển thị 1/1** hay "Đã hoàn thành tất cả bài tập Coding (1/1 bài)".
4. **Kết quả mong đợi tại Tab "Trắc nghiệm Game"**:
   - Thấy badge trạng thái **"Đã hoàn thành"** (thay vì "Đã xong 100%").
   - Thấy thẻ bài nộp Game:
     - Điểm số: `89 điểm` (không hiển thị `89 / 10`).
     - Số câu đúng: `6 / 10 câu (60%)` (tính tỷ lệ thực tế, không hiển thị `6 / 10 câu (100%)`).

---

### Kịch bản 2: Quản trị viên xem lịch sử chi tiết học viên Giác (`SubmissionHistoryModal`)
1. Đăng nhập với tài khoản Admin / Giảng viên.
2. Truy cập: `/dashboard/homeworks/79`.
3. Bấm xem lịch sử nộp bài chi tiết của học viên **Đỗ Quảng Giác** (ID: #59).
4. **Kết quả mong đợi trong Modal**:
   - Tiêu đề modal: **"Lịch sử nộp bài chi tiết 1/2 bài con"**.
   - Tab/Mục Coding: Hiển thị đúng **1/2 bài con** (gồm 2 bài coding thực tế).
   - Tuyệt đối **không xuất hiện bài "Bài tập chung"** trong danh mục bài tập con.
   - Mục/Tab Game Quiz hiển thị riêng biệt kết quả chơi game của học viên.
