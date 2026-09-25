# Bug Verification: Xóa Participant Khỏi Meeting Vẫn Bị Tạo Vi Phạm Vắng Mặt

- **Slug**: meeting-removed-participant-violation
- **Tested**: 2026-09-25T14:58:00+07:00
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

Bug đã được xử lý và kiểm chứng triệt để. Khi cập nhật danh sách participants của meeting để loại bỏ thành viên, hệ thống thực hiện hard delete bản ghi khỏi database, không còn nạp các bản ghi đã xóa vào Domain Entity (`_to_domain`, `to_entity`, `get_by_date`), và `AutomatedViolationHandler` được bảo vệ để không tạo vi phạm cho thành viên không còn trong meeting.

## Checks Performed

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| Reproduction (post-fix) | `test_check_meeting_attendance_decoupled_job` & `test_handle_meeting_absence_skips_violation_when_participant_not_found` | pass | Participant bị loại bỏ không còn kích hoạt `ParticipantAbsenceRecorded` và không bị tạo vi phạm |
| New / updated tests | `uv run pytest tests/test_meeting_use_cases.py tests/test_violation_event_handlers.py` | pass | Toàn bộ 9/9 tests mới và cập nhật đều PASS |
| Regression suite | `uv run pytest tests/test_meeting_use_cases.py tests/test_violation_event_handlers.py tests/test_violation_use_cases.py tests/test_billing_use_cases.py tests/test_homework_checker.py` | pass | 16/16 tests trong các module liên quan đều PASS |
| Lint / static check | `uv run ruff check app/meeting/infrastructure/repository.py app/meeting/infrastructure/model.py` | pass | Không có lỗi logic mới phát sinh |

## Output Excerpts

```text
============================= test session starts ==============================
platform darwin -- Python 3.12.2, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/nguyenhuynh/Documents/dut-ai-manager/backend
configfile: pyproject.toml
plugins: typeguard-4.4.1, anyio-4.9.0, Faker-33.1.0, asyncio-1.3.0
asyncio: mode=Mode.STRICT

tests/test_meeting_use_cases.py ...                                      [ 18%]
tests/test_violation_event_handlers.py ......                            [ 56%]
tests/test_violation_use_cases.py ..                                     [ 68%]
tests/test_billing_use_cases.py ....                                     [ 93%]
tests/test_homework_checker.py .                                         [100%]

======================== 16 passed, 2 warnings in 0.79s ========================
```

## Residual Risks

- Cơ sở dữ liệu hiện hữu có thể chứa một số bản ghi vi phạm cũ đã bị tạo sai trước khi áp dụng bản vá này nếu người dùng đã từng xóa participant khỏi meeting trước đây. Cần rà soát dữ liệu thủ công nếu cần dọn dẹp các vi phạm cũ.

## Recommendation

Đóng báo cáo lỗi — Bản vá đã được kiểm chứng end-to-end (verified). Toàn bộ luồng xóa participant với cơ chế hard delete và ngăn chặn tạo vi phạm sai đã hoạt động chính xác.
