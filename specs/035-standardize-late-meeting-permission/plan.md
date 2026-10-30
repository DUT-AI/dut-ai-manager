# Implementation Plan: Standardize Late Meeting Permission

**Branch**: `035-standardize-late-meeting-permission` | **Date**: 2026-10-31 | **Spec**: [specs/035-standardize-late-meeting-permission/spec.md](spec.md)

## Summary
Chuẩn hóa nghiệp vụ xin đi trễ (`RequestCategory.LATE`): Thêm domain invariants validation (`validate_late`), cập nhật trạng thái participant `LATE_EXCUSED` ngay khi tạo đơn, hoàn thiện cơ chế đối soát thời gian check-in UTC và xử lý vi phạm khi đi trễ quá giờ xin phép.

## Technical Context
- **Language/Version**: Python 3.12 (SQLAlchemy 2.0, Dishka DI, Pydantic V2).
- **Architecture**: Domain-Driven Design Invariants, Enterprise UTC comparison.
- **Constraints**: Không phá vỡ luồng điểm danh ESP32/Card, 100% unit tests pass.

## Implementation Tasks (Atomic Checklist)
- [ ] Task 1: Bổ sung domain validation `validate_late(meeting: Meeting)` trong `backend/app/permission_request/domain/entity.py`.
- [ ] Task 2: Thêm `mark_participant_late_excused` trong `backend/app/permission_request/infrastructure/repository.py`.
- [ ] Task 3: Tích hợp `MeetingRepository` và xử lý đơn `LATE` trong `backend/app/permission_request/application/create_permission_request_use_case.py`.
- [ ] Task 4: Cập nhật DI provider trong `backend/app/permission_request/providers.py`.
- [ ] Task 5: Cập nhật `delete_permission_request_use_case.py` để revert `LATE_EXCUSED` về `NOT_JOINED` khi xóa đơn.
- [ ] Task 6: Tinh chỉnh logic điểm danh `Participant.check_in` trong `backend/app/meeting/domain/entity.py` (nếu đến đúng giờ thì `JOINED`, nếu trễ trong hạn thì `LATE_EXCUSED`, quá hạn thì `LATE_UNEXCUSED`).
- [ ] Task 7: Thêm unit tests cho nghiệp vụ xin đi trễ (validate thời gian, cập nhật trạng thái, đối soát điểm danh).
- [ ] Task 8: Chạy kiểm thử toàn diện `pytest tests/unit/`.
