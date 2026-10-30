# Phase 0: Research & Decision Log

## Decision: Chuẩn hóa Domain Invariants cho LATE Permission Request
- **Context**: Trước đây, đơn xin đi trễ (`LATE`) chỉ lưu thông tin vào DB mà không có validation logic cụ thể nào như `POSTPONE` (kiểm tra bài tập hoãn $\le 4$ ngày). Đồng thời participant của buổi meeting cũng không được cập nhật trạng thái `LATE_EXCUSED`, dẫn đến việc UI hiển thị chưa chuẩn và xử lý điểm danh bị động.
- **Quyết định thiết kế**:
  1. Thêm phương thức `validate_late(meeting: Meeting)` vào Domain Entity `PermissionRequest`:
     - Kiểm tra `meeting.end_time > now` (không nộp đơn cho meeting đã kết thúc).
     - Kiểm tra `meeting.start_time < self.start_time <= meeting.end_time` (giờ dự kiến đến phải nằm trong khoảng thời gian diễn ra buổi họp).
  2. Tại `PermissionRequestRepository`:
     - Thêm phương thức `mark_participant_late_excused(meeting_id: int, user_id: int)` cập nhật status participant sang `LATE_EXCUSED` nếu hiện tại là `NOT_JOINED`.
     - Cập nhật `revert_participant_excused(meeting_id: int, user_id: int)` để khôi phục về `NOT_JOINED` khi hủy đơn `LATE` hoặc `ABSENCE`.
  3. Tại `CreatePermissionRequestUseCase`:
     - Inject thêm `MeetingRepository`.
     - Kiểm tra và thực thi `request.validate_late(meeting)`.
     - Cập nhật participant sang `LATE_EXCUSED`.
  4. Tại `Participant.check_in`:
     - Nếu học viên đến đúng giờ (`check_in_at <= meeting_start_time`), dù có đơn xin trễ vẫn công nhận `JOINED` (Đúng giờ).
     - Nếu đến sau giờ bắt đầu: Nếu có đơn xin trễ còn hiệu lực (`check_in_at <= expected_arrival_time`), ghi nhận `LATE_EXCUSED` (Không phạt). Nếu vượt quá giờ xin phép, ghi nhận `LATE_UNEXCUSED` (Phạt vi phạm).
