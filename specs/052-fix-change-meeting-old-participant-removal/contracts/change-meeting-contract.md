# Interface Contract: Luồng Đổi Buổi Sinh Hoạt (`CHANGE_MEETING`)

## 1. Giao Thức API Tạo Đơn Xin Phép

### Endpoint
`POST /api/v1/permissions`

### Request Body (`PermissionRequestCreate`) - Giữ nguyên không đổi
```json
{
  "category": "CHANGE_MEETING",
  "meeting_id": 522,
  "old_meeting_id": 520,
  "note": "Em xin phép đổi sang ca Chủ Nhật do lịch học đột xuất"
}
```

### Quy Tắc Thẩm Định (Validation Rules) - Giữ nguyên không đổi
1. `meeting_id` (Bắt buộc): Buổi họp đích phải tồn tại, chưa đến giờ bắt đầu (`now < meeting_b.start_time`), và còn ghế trống (`available_seats > 0`).
2. `old_meeting_id` (Tùy chọn):
   - Nếu có `old_meeting_id`: Phải khác `meeting_id`.
   - Nếu không có: Hệ thống xem là đăng ký mới (không thực hiện auto-discovery hay validation bổ sung theo yêu cầu).

---

## 2. Phản Ứng Trạng Thái Dữ Liệu (State Transitions & Side Effects)

1. **Buổi họp cũ (`old_meeting_id`)**:
   - `ParticipantRepository.remove_participant(old_meeting_id, user_id)` được gọi trực tiếp.
   - Bản ghi `(meeting_id = old_meeting_id, user_id = user_id)` bị xóa khỏi bảng `meeting_participants`.
   - `PermissionRequestRepository.cancel_active_requests_by_meeting(user_id, old_meeting_id)` hủy mềm các đơn vắng/trễ cũ tại buổi họp đó.
2. **Buổi họp mới (`meeting_id`)**:
   - `ParticipantRepository.add_participant(...)` được gọi trực tiếp với `status = 'NOT_JOINED'`, `role = 'TRAINEE'`.
3. **Phát Domain Events**:
   - `MeetingParticipantTransferred(request_id, user_id, old_meeting_id, new_meeting_id, note)`
   - `PermissionRequestCreated(...)`
