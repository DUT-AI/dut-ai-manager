# Quickstart: Hướng Dẫn Kiểm Thử và Xác Minh Tính Năng Refactor Repository

## 1. Mục Tiêu Kiểm Thử
Xác minh rằng sau khi phân tách `MeetingRepository` và `ParticipantRepository`:
1. `ChangeMeetingStrategy` xóa trực tiếp học viên khỏi `meeting_participants` tại buổi cũ bằng `participant_repo.remove_participant` và thêm vào buổi mới bằng `participant_repo.add_participant`.
2. `CreateMeetingUseCase` và `UpdateMeetingUseCase` hoạt động trơn tru với `participant_repo.bulk_create` và `participant_repo.sync_meeting_participants`.
3. Không làm thay đổi hay ảnh hưởng đến bất kỳ luồng nào khác.

---

## 2. Kịch Bản Kiểm Thử Tự Động (Automated Tests)

### Chạy Unit Test Cho `ChangeMeetingStrategy`
```bash
cd backend
poetry run pytest tests/unit/test_change_meeting_permission_request.py -v
```

### Chạy Integration Test API Cho `CHANGE_MEETING`
```bash
cd backend
poetry run pytest tests/api/test_change_meeting_api.py -v
```

### Chạy Toàn Bộ Test Suite Liên Quan Đến Meeting Use Cases
```bash
cd backend
poetry run pytest tests/unit/test_meeting_use_cases.py tests/api/test_meeting_api.py -v
```
