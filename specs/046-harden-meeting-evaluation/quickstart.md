# Quickstart Validation Guide: Tinh giản Đánh giá Meeting

**Feature Branch**: `046-harden-meeting-evaluation`  
**Ngày thực hiện**: 2026-11-04  
**Trạng thái**: Sẵn sàng kiểm thử (Ready for Validation)

Tài liệu này hướng dẫn cách chạy và xác minh tính năng sau khi triển khai thực tế.

---

## 1. Điều kiện tiên quyết (Prerequisites)

- **Backend**: Python 3.12+, Poetry, PostgreSQL database đã chạy migration.
- **Frontend**: Node.js 18+, npm/npx.

---

## 2. Kiểm thử Tự động (Automated Verification)

### Bước 1: Kiểm thử Backend Unit & API Tests
Chạy toàn bộ test suite liên quan đến meeting evaluation và API meeting:

```bash
cd backend
poetry run pytest tests/unit/test_meeting_evaluation.py tests/api/test_meeting_api.py -v
```

**Kỳ vọng**:
- `test_submit_trainee_evaluation_self_eval_blocked`: Pass (400 Bad Request "Không thể tự đánh giá chính mình").
- `test_submit_trainee_evaluation_invalid_trainer_blocked`: Pass (400 Bad Request "Người được đánh giá không phải là Trainer của buổi học này").
- `test_submit_overall_evaluation_unauthorized_blocked`: Pass (403 Forbidden cho user không phải Trainer/Admin).
- `test_get_meeting_evaluation_summary_without_fake_optional`: Pass (Khởi tạo `GetMeetingEvaluationSummaryUseCase` với 3 repo bắt buộc).
- Toàn bộ 48+ test cases đều đạt trạng thái **PASSED**.

### Bước 2: Kiểm thử Frontend Type Checking & Build
Chạy TypeScript check và build production để đảm bảo không còn import lỗi từ `TrainerEvaluationModal.tsx` đã xóa:

```bash
cd frontend
npx tsc --noEmit
npm run build
```

**Kỳ vọng**:
- 0 lỗi TypeScript (`Found 0 errors`).
- Bundle build thành công sạch sẽ.

---

## 3. Kịch bản Xác minh Trực quan (Manual E2E Scenarios)

### Kịch bản 1: Giảng viên chỉ gửi 1 Đánh giá tổng thể lớp học
1. Đăng nhập với tài khoản **Giảng viên** (Trainer phụ trách buổi học).
2. Mở trang chi tiết buổi học `MeetingDetailPage`:
   - Kiểm tra **Header**: Nhìn thấy nút "Trainer đánh giá buổi học" (hoặc "Xem Đánh giá tổng thể" nếu đã gửi) và thông tin `Hạn chót đánh giá` cụ thể.
   - Kiểm tra tab **Thành viên** (`MeetingParticipantsTab`):
     - Không còn cột "Đánh giá của Trainer" trong bảng `TraineeListTable`.
     - Không còn nút bấm "Chấm điểm" / "Đã ĐG" cạnh từng dòng học viên trong `ParticipantActionButtons`.
     - Component `TrainerEvaluationModal` không còn xuất hiện.
3. Bấm "Trainer đánh giá buổi học", chấm điểm 4 tiêu chí cho toàn bộ lớp học và gửi.
4. Gửi thành công, hệ thống hiển thị điểm tổng thể của cả lớp ngay trên view báo cáo.

### Kịch bản 2: Học viên đánh giá Giảng viên & Chặn tự đánh giá
1. Đăng nhập với tài khoản **Học viên** (Trainee đã check-in tham gia buổi học).
2. Mở trang chi tiết buổi học:
   - Trên Header hoặc Banner, bấm "Đánh giá Trainer ngay".
   - Thấy modal chọn Trainer (nếu buổi học có nhiều Trainer) và chấm 4 tiêu chí.
   - Gửi đánh giá thành công.
3. Thử nghiệm gian lận tự đánh giá:
   - Gọi API `POST /api/v1/meetings/{id}/evaluations/trainee` với `target_user_id` chính là user của mình.
   - Hệ thống phản hồi ngay lập tức `400 Bad Request: "Không thể tự đánh giá chính mình"`.

### Kịch bản 3: Tối ưu hiệu năng truy vấn
1. Bật log SQL tại backend (`echo=True` hoặc log SQLAlchemy queries).
2. Gửi request `POST /api/v1/meetings/{id}/evaluations/overall`.
3. Kiểm tra số lượng câu truy vấn `SELECT` vào bảng `meetings`:
   - Chỉ xuất hiện **1 lần** truy vấn `SELECT` thực thể `meeting` (thay vì 2 lần lặp lại như trước).
