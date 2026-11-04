# Nghiên Cứu Kỹ Thuật: Điều Chỉnh Thời Hạn Đánh Giá Cuộc Họp Từ 72 Giờ Về 24 Giờ

**Feature**: `051-meeting-evaluation-deadline-24h`  
**Ngày**: 2026-11-05  
**Trạng thái**: Hoàn thành nghiên cứu

---

## 1. Bối Cảnh Nghiệp Vụ & Đánh Giá Tác Động (Impact Analysis)

Hiện tại, hệ thống quản lý học tập và sinh hoạt (`dut-ai-manager`) áp dụng chính sách đánh giá sau cuộc họp (bao gồm học viên đánh giá Trainer và Trainer đánh giá tổng thể buổi học).
Trước đây, thời hạn hoàn thành đánh giá được đặt là 72 giờ (3 ngày) sau khi cuộc họp kết thúc (`meeting.end_time`).
Yêu cầu mới: **Rút ngắn thời hạn bắt buộc đánh giá từ 72 giờ xuống 24 giờ (1 ngày)**.

### Phân tích các vị trí tác động trong mã nguồn:
1. **Domain Layer**:
   - `backend/app/meeting/domain/constants.py`: Hằng số `MEETING_EVALUATION_DEADLINE_HOURS: int = 72` cần đổi thành `24`.
   - `backend/app/meeting/domain/__init__.py`: Re-export `MEETING_EVALUATION_DEADLINE_HOURS`.
2. **Application Layer**:
   - `backend/app/meeting/application/check_evaluation_deadline_job_use_case.py`:
     - Ngưỡng lọc cuộc họp: `end_bound = now - timedelta(hours=MEETING_EVALUATION_DEADLINE_HOURS)` (tự động nhận giá trị 24h).
     - Chuỗi lý do vi phạm của Trainee: `"Chưa hoàn thành đánh giá Trainer cho buổi học '{meeting.title}'{time_str} trong vòng 72h"` -> chuyển thành `"trong vòng 24h"`.
     - Chuỗi lý do vi phạm của Trainer: `"Trainer chưa hoàn tất đánh giá tổng thể buổi học '{meeting.title}'{time_str} trong vòng 72h"` -> chuyển thành `"trong vòng 24h"`.
3. **Infrastructure & Job Layer**:
   - `backend/app/jobs/meeting_evaluation_checker_job.py`: Docstring và log cập nhật 72h -> 24h.
   - `backend/app/core/scheduler.py`: Cập nhật job name từ `"Check 72h meeting evaluations deadline"` thành `"Check 24h meeting evaluations deadline"`.
4. **Testing Layer**:
   - `backend/tests/unit/test_meeting_evaluation.py`:
     - Cập nhật assertion lý do vi phạm `"trong vòng 24h"`.
     - Cập nhật test case kiểm tra bounds thời gian: `test_check_evaluation_deadline_uses_24h_bound_and_9d_window`.

---

## 2. Quyết Định Kỹ Thuật (Architecture Decisions)

### Quyết định 1: Giữ nguyên cơ chế Domain Constant tập trung
- **Giải pháp**: Giá trị 24h được định nghĩa tập trung duy nhất tại `MEETING_EVALUATION_DEADLINE_HOURS: int = 24` trong `app.meeting.domain.constants`.
- **Lý do**: Tuân thủ triệt để Clean Architecture và Single Source of Truth (Principle X). Không hardcode số 24 ở bất kỳ logic tính toán ngày giờ nào.

### Quyết định 2: Tương thích ngược với các bản ghi vi phạm cũ
- **Giải pháp**: Cơ chế kiểm tra trùng lặp vi phạm dựa trên `violation_repo.exists_by_user_and_reason(user_id, reason)`.
  - Các vi phạm cũ mang lý do `"trong vòng 72h"` đã ghi nhận trong quá khứ được giữ nguyên vẹn để làm bằng chứng lịch sử.
  - Các vi phạm mới phát sinh kể từ khi cập nhật sẽ mang lý do `"trong vòng 24h"`.
  - Không cần sửa đổi dữ liệu bảng `violations` hay viết migration cơ sở dữ liệu.

### Quyết định 3: Tần suất quét định kỳ (Scan Frequency)
- **Giải pháp**: Giữ nguyên tần suất quét của APScheduler là **mỗi giờ 1 lần** (`CronTrigger(minute=0, timezone="Asia/Ho_Chi_Minh")`).
- **Lý do**: Với thời hạn 24 giờ, việc quét mỗi giờ đảm bảo ngay khi cuộc họp vừa bước qua mốc 24h00m, trong tối đa 59 phút tiếp theo hệ thống sẽ phát hiện và ghi nhận vi phạm kịp thời.

---

## 3. Rủi Ro Kỹ Thuật & Biện Pháp Kiểm Soát

| Rủi ro tiềm ẩn | Biện pháp kiểm soát |
| :--- | :--- |
| **Ghi nhận trùng lặp vi phạm cho cuộc họp cũ** | Hàm quét chỉ lấy các cuộc họp trong cửa sổ từ `now - 9 days` đến `now - 24 hours` và có bước kiểm tra `exists_by_user_and_reason`. |
| **Sai lệch múi giờ khi tính mốc 24 giờ** | Sử dụng `datetime.now(timezone.utc)` theo chuẩn Hiến pháp Principle III để trừ `timedelta(hours=24)`. |
| **Lỗi hồi quy bộ kiểm thử** | Chạy toàn bộ test suite `backend/tests/unit/test_meeting_evaluation.py` để đảm bảo 100% test pass. |
