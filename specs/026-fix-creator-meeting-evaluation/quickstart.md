# Quickstart & Verification Guide: Đánh giá buổi sinh hoạt cho Người tạo cuộc họp

**Feature**: `026-fix-creator-meeting-evaluation`  
**Date**: 2026-10-24  
**Status**: Ready for Validation  

---

## 1. Chuẩn bị môi trường & Dữ liệu kiểm thử

Tài khoản kiểm thử cần thiết:
1. **Người tạo buổi học (User A)**: Tài khoản thành viên thông thường (hoặc Trainer), **không có vai trò Admin / Leader / Manager**.
2. **Học viên tham dự (User B)**: Tài khoản thành viên bình thường tham gia lớp học.
3. **Quản trị viên (User Admin)**: Tài khoản có role `admin`.

---

## 2. Các kịch bản xác minh (Validation Scenarios)

### Kịch bản 1: Tạo buổi học và kiểm tra phản hồi DTO
1. Đăng nhập với tài khoản **User A**.
2. Thực hiện tạo một buổi học mới:
   - Tiêu đề: `Buổi kiểm thử phân quyền đánh giá`
   - Thời gian bắt đầu: Quá khứ 2 tiếng (hoặc hiện tại).
   - Thời gian kết thúc: Quá khứ 30 phút (đã kết thúc).
   - Bật tùy chọn `enable_evaluation: true`.
   - Mời **User B** tham gia.
3. **Kết quả mong đợi**:
   - API trả về `created_by` bằng chính `id` của **User A**.
   - Đối tượng `trainer` trong response có `id` trùng với `id` của **User A**.

---

### Kịch bản 2: Kiểm tra hiển thị nút đánh giá trên Giao diện Web (User A)
1. Đăng nhập bằng tài khoản **User A** trên Web Frontend.
2. Truy cập trang chi tiết buổi học vừa tạo tại `/dashboard/meetings/{id}`.
3. **Kết quả mong đợi**:
   - Thanh tiêu đề (Header): Hiển thị nút **"Trainer đánh giá buổi học"** (màu hổ phách hoặc xanh lá nếu đã đánh giá).
   - Bảng thành viên (Participants Tab): Dòng của **User B** hiển thị nút **"Đánh giá"** (hoặc "Đã ĐG").
   - Nút chỉnh sửa buổi học hiển thị đầy đủ (do User A là chủ sở hữu buổi học).

---

### Kịch bản 3: Thực hiện đánh giá tổng thể và chấm điểm học viên (User A)
1. Trên giao diện của **User A**, nhấn nút **"Trainer đánh giá buổi học"**:
   - Điền nhận xét và chấm điểm các tiêu chí (1-5 sao).
   - Nhấn **"Gửi đánh giá"**.
   - **Kết quả**: Gửi thành công, nhận thông báo `Đánh giá tổng thể buổi học thành công`, nút đổi trạng thái thành `✓ Đã đánh giá buổi học`.
2. Trong bảng danh sách thành viên, nhấn nút **"Đánh giá"** tại dòng của **User B**:
   - Chấm điểm 4 tiêu chí và nhập nhận xét.
   - Nhấn **"Lưu đánh giá"**.
   - **Kết quả**: Gửi thành công, điểm số hiển thị ngay trên bảng.

---

### Kịch bản 4: Kiểm tra phân quyền an toàn đối với Học viên (User B)
1. Đăng nhập với tài khoản **User B** (học viên tham dự).
2. Truy cập trang chi tiết buổi học.
3. **Kết quả mong đợi**:
   - Header **không** hiển thị nút "Trainer đánh giá buổi học".
   - Header hiển thị nút **"Đánh giá Trainer"** và nút **"Điểm của tôi"**.
   - Bảng thành viên **không** có các nút chấm điểm của Trainer.

---

### Kịch bản 5: Chống leo thang quyền hạn qua API (Security Gate)
1. Sử dụng token của **User B** gửi request trực tiếp:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/meetings/{id}/evaluations/overall" \
     -H "Authorization: Bearer <TOKEN_USER_B>" \
     -H "Content-Type: application/json" \
     -d '{"scores":[{"criteria_code":"ORGANIZATION","score":5}],"general_feedback":"hack"}'
   ```
2. **Kết quả mong đợi**:
   - API trả về HTTP Status `403 Forbidden` với thông báo: `Bạn không có quyền đánh giá buổi học này`.

---

## 3. Lệnh kiểm thử tự động (Automated Verification Commands)

### Backend Pytest Suite
```bash
# Chạy bộ test cho chức năng đánh giá meeting và phân quyền
pytest backend/tests/unit/test_meeting_evaluation.py -v
pytest backend/tests/api/test_meeting_api.py -k "evaluation" -v
```

### Frontend Build & Lint Verification
```bash
# Đảm bảo frontend TypeScript biên dịch không lỗi
cd frontend && npm run build
```
