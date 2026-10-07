# Quickstart & Verification Guide: Đơn Xin Đổi Buổi Sinh Hoạt / Meeting (`CHANGE_MEETING`)

**Branch**: `007-change-meeting-permission-request` | **Date**: 2026-10-07

Tài liệu này hướng dẫn cách chạy kiểm thử tự động và xác minh thực tế tính năng `CHANGE_MEETING`.

---

## 1. Prerequisites & Environment Setup

- Docker / PostgreSQL đang chạy.
- Backend dependencies đã cài đặt (`pip install -r requirements.txt`).
- Migration database đã được áp dụng:
  ```bash
  cd backend
  alembic upgrade head
  ```

---

## 2. Automated Test Suite Execution

Chạy toàn bộ test cases cho Use Case, Domain và Controller:

```bash
cd backend
pytest tests/test_change_meeting_permission_request.py -v
```

---

## 3. End-to-End Test Scenarios

### Kịch bản 1: Chuyển ca thành công từ Meeting A sang Meeting B còn chỗ

1. **Chuẩn bị**:
   - Meeting A (ID 101): Bắt đầu sau 2 ngày, User 1 là participant.
   - Meeting B (ID 102): Bắt đầu sau 3 ngày, hiện có 20 participant (còn 15 ghế).
   - User 1 đang có 01 đơn xin vắng (`ABSENCE`) tại Meeting A.
2. **Thực thi**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/permission-requests \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <TOKEN_USER_1>" \
     -d '{
       "category": "CHANGE_MEETING",
       "old_meeting_id": 101,
       "meeting_id": 102,
       "note": "Bận lịch thi sáng T7 xin chuyển sang ca CN"
     }'
   ```
3. **Kỳ vọng**:
   - HTTP Status: `200 OK`.
   - User 1 được rút khỏi danh sách participant của Meeting 101.
   - User 1 xuất hiện trong danh sách participant của Meeting 102 với status `NOT_JOINED`.
   - Đơn xin vắng cũ tại Meeting 101 bị đánh dấu xóa (`is_deleted = True`).
   - Event `MeetingParticipantTransferred` được publish và kích hoạt gửi thông báo.

---

### Kịch bản 2: Từ chối khi Meeting B đã hết ghế trống

1. **Chuẩn bị**:
   - Meeting B (ID 103): Đang có 35 participant active (không có đơn ABSENCE nào), ghế còn lại = 0.
2. **Thực thi**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/permission-requests \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <TOKEN_USER_2>" \
     -d '{
       "category": "CHANGE_MEETING",
       "meeting_id": 103,
       "note": "Xin vào ca tối"
     }'
   ```
3. **Kỳ vọng**:
   - HTTP Status: `400 Bad Request`.
   - Response message: `"Buổi họp đích đã hết chỗ ngồi (0/35)"`.
   - Không có thay đổi nào trong bảng `meeting_participants`.

---

### Kịch bản 3: Từ chối khi Meeting B đã bắt đầu / kết thúc

1. **Chuẩn bị**:
   - Meeting B (ID 104): `start_time` trong quá khứ so với thời điểm hiện tại.
2. **Thực thi**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/permission-requests \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <TOKEN_USER_1>" \
     -d '{
       "category": "CHANGE_MEETING",
       "meeting_id": 104,
       "note": "Xin vào bù"
     }'
   ```
3. **Kỳ vọng**:
   - HTTP Status: `400 Bad Request`.
   - Response message: `"Không thể đổi sang buổi họp đã bắt đầu hoặc đã kết thúc"`.

---

### Kịch bản 4: Kiểm tra API lấy danh sách buổi họp kèm số ghế khả dụng

1. **Thực thi**:
   ```bash
   curl -X GET http://localhost:8000/api/v1/meetings/available-seats \
     -H "Authorization: Bearer <TOKEN>"
   ```
2. **Kỳ vọng**:
   - Trả về mảng các Meeting sắp tới kèm các trường: `max_seats`, `occupied_seats`, `available_seats`, `is_full`.
