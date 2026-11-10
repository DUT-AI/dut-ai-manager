# Phase 0: Research - Bắt buộc chọn ca hiện tại và kiểm tra sự hiện diện

## Problem Analysis & Scope

Trước đây trong Feature 007 (`change-meeting-permission-request`), hệ thống cho phép `old_meeting_id: int | None = None` để hỗ trợ trường hợp "đăng ký mới vào một ca meeting khi chưa có lịch".
Tuy nhiên, điều này gây ra lỗ hổng nghiệp vụ:
- Học viên có thể đổi sang ca khác mà không cần chứng minh mình đang ở ca nào.
- Học viên có thể chọn bừa một ca hiện tại mà mình không hề có mặt để chuyển đi.
- Làm sai lệch việc quản lý chỗ ngồi (`available_seats`), vì ca chuyển đi không giải phóng chỗ ngồi thực sự, nhưng ca đích lại bị chiếm thêm chỗ.

## Architectural Decisions

1. **Strict Payload Contract (`ChangeMeetingPayload`)**:
   - Chuyển `old_meeting_id: int` thành trường bắt buộc (không nhận `None`).
   - `meeting_id: int` là ca đích (bắt buộc).

2. **Validation Logic trong `ChangeMeetingStrategy.validate`**:
   - Lấy thông tin `old_meeting_id` từ payload và `user_id = request.created_by`.
   - Gọi `old_meeting = self.meeting_repo.get_by_id(old_meeting_id)`.
     - Nếu không tìm thấy: Raise `HTTPException(status_code=404, detail="Không tìm thấy buổi sinh hoạt hiện tại đã chọn")`.
   - Kiểm tra `user_id` trong `old_meeting.participants`:
     - Phải tồn tại một participant có `p.user_id == user_id` và `not p.is_deleted`.
     - Nếu KHÔNG tồn tại: Raise `HTTPException(status_code=400, detail="Bạn không có mặt trong danh sách tham gia của buổi sinh hoạt hiện tại đã chọn")`.

3. **Frontend Web & Zalo Mini App**:
   - `PermissionFormModal.tsx` trên Web:
     - `Form.Item` cho `old_meeting_id` chuyển `rules: [{ required: true, message: 'Vui lòng chọn buổi sinh hoạt hiện tại!' }]`.
     - Xóa bỏ tùy chọn rỗng `allowClear` và tooltip "để trống nếu đăng ký mới".
     - Lọc danh sách `meetings`: Hiển thị ưu tiên hoặc lọc các buổi họp mà `user` hiện tại đang tham gia.
   - `PermissionFormModal.tsx` trên Zalo Mini App:
     - Chuyển nhãn thành có dấu `*`.
     - Xóa bỏ option "Chưa có buổi học nào (Đăng ký mới)".
     - Thêm kiểm tra chặn submit nếu `!formOldMeetingId`.

4. **Cập nhật Unit / Integration Tests**:
   - Cập nhật test case cũ `test_change_meeting_new_registration_without_old_meeting` thành kiểm thử từ chối khi thiếu `old_meeting_id`.
   - Thêm test case mới: `test_change_meeting_rejects_when_user_not_participant_in_old_meeting`.
