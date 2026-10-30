# Implementation Plan: Unified Meeting Check-In Domain Entity Refactor

**Branch**: `029-meeting-checkin-domain-refactor`  
**Tracking Issue / Spec**: [spec.md](spec.md)  
**Status**: DRAFT -> READY FOR REVIEW

---

## 1. Technical Context & Overview

### Current State & Architecture Gaps
1. **Domain Layer Anemia**:
   - `MeetingParticipant.check_in()` trong `app/meeting/domain/entity.py` bị lặp điều kiện và return sớm khi status là `LATE_EXCUSED`, `LATE_UNEXCUSED`, `JOINED`, `COMPLETED` mà không cập nhật `check_in_at` hay `link_image`.
   - Quyết định `is_late` và phân bổ status không nằm trong Entity mà bị dàn trải ra các Use Case.
2. **Use Case Duplication & Drift**:
   - `CheckInUseCase`: Tính toán `is_late = meeting.is_late(check_in_dt)`, nhưng khi gọi `participant.check_in` lại truyền cứng `status=ParticipantStatus.JOINED`. Lấy `window_start`/`window_end` theo `now` thay vì `check_in_dt`.
   - `CheckInWithCardUseCase`: Tự quản lý `status=ParticipantStatus.JOINED` và tự tính `is_late`.
   - `UpdateParticipantStatusUseCase`: Điểm danh thủ công có logic `update_attendance_status` riêng.
3. **Repository Persistence Omission**:
   - `ParticipantRepository.save` trong `app/meeting/infrastructure/repository.py` không map `orm.client_event_id = domain.client_event_id`.

### Desired Architecture (Clean Architecture / DDD)
```
[Client (Face AI / Card RFID / Web Admin)]
                 │
                 ▼
          [Controller / API]
                 │
                 ▼
[CheckInUseCase / CheckInWithCardUseCase / UpdateParticipantStatusUseCase]
   │ (1. Parse / ensure UTC datetime)
   │ (2. Fetch Meeting & Participant from Repository)
   │ (3. Delegate to Domain Entity)
   ▼
[MeetingParticipant (Domain Entity)]
   │ └── record_check_in(check_in_time, meeting_start_time, image_url, client_event_id)
   │       ├── Enforce state transitions & business invariants
   │       ├── Preserve LATE_EXCUSED while recording check_in_at & image_url
   │       ├── Auto-determine JOINED vs LATE_UNEXCUSED
   │       └── Return (success, message, is_late)
   ▼
[ParticipantRepository]
   │ └── save(participant) -> Persists status, check_in_at, check_out_at, link_image, client_event_id
   ▼
[EventBus]
   └── publish(ParticipantCheckedIn)
```

---

## 2. Constitution Check

- **I. Clean Architecture & Practical DDD Boundaries (MUST)**: ✅ **Compliant**. Toàn bộ luật nghiệp vụ được đưa về Domain Entity `MeetingParticipant`. Use Case chỉ đóng vai trò Orchestrator, Repository thuần túy lưu trữ.
- **II. Dependency Injection with Dishka (MUST)**: ✅ **Compliant**. Giữ nguyên Dishka injection hiện tại, không thêm bớt dependency bừa bãi.
- **III. Enterprise UTC Storage & Vietnam Display Integrity (MUST)**: ✅ **Compliant**. Mọi mốc thời gian `check_in_at` và `check_in_time` truyền vào Entity đều là Timezone-Aware UTC qua `_ensure_utc` hoặc `parse_datetime_to_utc`.
- **IV. Event-Driven Decoupling (MUST)**: ✅ **Compliant**. Bắn sự kiện `ParticipantCheckedIn` qua EventBus sau khi lưu DB thành công.
- **VI. Idempotency & Network Resilience (MUST)**: ✅ **Compliant**. Persist `client_event_id` vào ORM Model trong Repository để chống trùng lặp sự kiện mạng.
- **X. Zero Redundant Backward Compatibility (MUST)**: ✅ **Compliant**. Cập nhật trực tiếp call-sites, không tạo wrapper thừa.

---

## 3. Phase Breakdown & Implementation Steps

### Phase 0: Research & Boundary Definition
- **Artifact**: `specs/029-meeting-checkin-domain-refactor/research.md`
- Phân tích toàn bộ các trạng thái của `ParticipantStatus`: `NOT_JOINED`, `JOINED`, `LATE_EXCUSED`, `LATE_UNEXCUSED`, `ABSENT_EXCUSED`, `ABSENT_UNEXCUSED`, `COMPLETED`.
- Xác định ma trận chuyển đổi trạng thái (State Transition Matrix) khi check-in.

### Phase 1: Data Model & Contracts
- **Artifacts**: 
  - `specs/029-meeting-checkin-domain-refactor/data-model.md`
  - `specs/029-meeting-checkin-domain-refactor/quickstart.md`
- Thiết kế phương thức nghiệp vụ chuẩn trên `MeetingParticipant`:
  ```python
  def record_check_in(
      self,
      check_in_time: datetime,
      meeting_start_time: datetime,
      image_url: str | None = None,
      client_event_id: str | None = None,
  ) -> tuple[bool, str, bool]:
  ```

### Phase 2: Domain Entity Refactoring & Unit Tests (TDD)
1. Viết bộ unit test toàn diện cho `MeetingParticipant.record_check_in` trong `tests/unit/test_meeting_use_cases.py` (hoặc `test_meeting_domain.py`):
   - Check-in đúng giờ (`check_in_time <= meeting_start_time`) $\rightarrow$ `status = JOINED`, `check_in_at = check_in_time`.
   - Check-in trễ không phép (`check_in_time > meeting_start_time`) $\rightarrow$ `status = LATE_UNEXCUSED`, `check_in_at = check_in_time`, `is_late = True`.
   - Check-in khi đã có đơn xin đi trễ (`status == LATE_EXCUSED`) $\rightarrow$ giữ nguyên `status = LATE_EXCUSED`, cập nhật `check_in_at = check_in_time`, lưu `link_image`.
   - Check-in khi đã `COMPLETED` $\rightarrow$ trả về `(False, ..., False)`.
   - Check-in cập nhật lại ảnh khi đã `JOINED` $\rightarrow$ cho phép cập nhật ảnh mới.
2. Triển khai phương thức trong `backend/app/meeting/domain/entity.py`.

### Phase 3: Repository Persistence Enhancement
1. Cập nhật `ParticipantRepository.save` trong `backend/app/meeting/infrastructure/repository.py`:
   - Bổ sung `orm.client_event_id = domain.client_event_id`.
   - Đảm bảo mapper `from_entity` và `to_entity` đồng bộ đầy đủ các trường.

### Phase 4: Use Case Orchestrator Simplification
1. Refactor `backend/app/meeting/application/checkin_use_case.py`:
   - Dùng `check_in_dt` để tính `window_start = check_in_dt - half_hour` và `window_end = check_in_dt + half_hour`.
   - Gọi `participant.record_check_in(check_in_time=check_in_dt, meeting_start_time=meeting.start_time, image_url=image_url, client_event_id=client_event_id)`.
   - Lưu qua repo và bắn `ParticipantCheckedIn(..., is_late=is_late, check_in_at=participant.check_in_at)`.
2. Refactor `backend/app/meeting/application/checkin_with_card_use_case.py`:
   - Gọi `participant.record_check_in(check_in_time=now, meeting_start_time=meeting.start_time)`.
   - Giữ nguyên cơ chế phát âm thanh TTS phù hợp với kết quả trả về.

### Phase 5: Verification & Zero Regression
1. Chạy toàn bộ Unit Tests: `uv run --directory backend pytest tests/unit/`.
2. Kiểm tra linter Ruff: `uv run --directory backend ruff check app/`.
3. Kiểm tra Frontend compilation: `npm --prefix frontend run build`.
