# Bug Fix: Hard Delete Khi Cập Nhật Participants Meeting & Ngăn Tạo Vi Phạm Vắng Sai

- **Slug**: meeting-removed-participant-violation
- **Fixed**: 2026-09-25T14:57:00+07:00
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

Đã chuyển đổi cơ chế cập nhật danh sách participants của meeting sang hard delete (xóa hẳn bản ghi khỏi bảng `meeting_participants` khi bị loại bỏ), đồng thời bổ sung bộ lọc `is_deleted` ở tầng mapper (`to_entity`, `_to_domain`, `get_by_date`) và cơ chế phòng vệ tại `AutomatedViolationHandler` để ngăn chặn hoàn toàn việc tạo vi phạm vắng mặt cho các thành viên đã bị xóa.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `backend/app/meeting/infrastructure/repository.py` | modified | Sử dụng `session.delete` (hard delete) cho participant bị loại khỏi meeting; lọc `is_deleted == False` trong `_to_domain` và `get_by_date` |
| `backend/app/meeting/infrastructure/model.py` | modified | Lọc bỏ các `is_deleted == True` participant trong `Meeting.to_entity()` |
| `backend/app/violation/application/event_handlers.py` | modified | Dừng và bỏ qua việc tạo vi phạm nếu không cập nhật được trạng thái participant (participant không tồn tại/đã bị xóa) |
| `backend/tests/test_meeting_use_cases.py` | modified | Bổ sung unit tests cho hard delete khi save meeting và mapper filtering |
| `backend/tests/test_violation_event_handlers.py` | modified | Bổ sung unit test xác nhận bỏ qua tạo vi phạm khi participant không tồn tại trong meeting |

## Diff Highlights (optional)

```python
# backend/app/meeting/infrastructure/repository.py
# 1. Hard delete participants not in the new list
for old_user_id, old_p in existing_user_ids.items():
    if old_user_id not in new_user_ids:
        self.session.delete(old_p)
```

```python
# backend/app/violation/application/event_handlers.py
if self.participant_repo:
    try:
        self.participant_repo.update_participant_status(
            meeting_id=event.meeting_id,
            user_id=event.user_id,
            status=ParticipantStatus.ABSENT_UNEXCUSED,
        )
    except Exception as e:
        logger.warning(
            f"Could not update participant status for user {event.user_id} in meeting {event.meeting_id}: {e}. Skipping violation creation."
        )
        return
```

## Tests Added or Updated

- `backend/tests/test_meeting_use_cases.py::test_meeting_repository_save_hard_deletes_removed_participants` — Xác nhận `MeetingRepository.save` gọi `session.delete` cho các participant bị loại bỏ.
- `backend/tests/test_meeting_use_cases.py::test_meeting_mapping_filters_is_deleted_participants` — Xác nhận `to_entity()` và `_to_domain()` không nạp participant bị soft-delete.
- `backend/tests/test_violation_event_handlers.py::test_handle_meeting_absence_skips_violation_when_participant_not_found` — Xác nhận không tạo vi phạm khi participant không tồn tại/bị xóa trong meeting.

## Local Verification

- Commands run: `uv run pytest tests/test_meeting_use_cases.py tests/test_violation_event_handlers.py` → **9 passed, 2 warnings in 0.77s**
- Toàn bộ test suite liên quan đến Meeting và Violation event handlers đều chạy thành công.

## Deviations from Assessment

- Theo yêu cầu trực tiếp từ người dùng, thay vì giữ soft delete cho participants khi cập nhật meeting, hệ thống đã chuyển sang thực hiện **Hard Delete** (`session.delete(old_p)`) khi xóa participant khỏi meeting.

## Follow-ups

- Dọn dẹp/kiểm tra dữ liệu các vi phạm vắng họp đã lỡ tạo trước đó cho các participant bị xóa trong DB (nếu có).
