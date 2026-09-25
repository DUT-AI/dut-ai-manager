# Bug Assessment: Xóa Participant Khỏi Meeting Vẫn Bị Tạo Vi Phạm Vắng Mặt

- **Slug**: meeting-removed-participant-violation
- **Created**: 2026-09-25T14:50:40+07:00
- **Source**: pasted text
- **Verdict**: valid
- **Severity**: high

## Report (verbatim or summarized)

> "Hiện tại khi tôi cập nhật danh sách các participant của 1 meeting bằng cách xóa 1 vài người thì gặp lỗi, vẫn tạo vi phạm khi không tham gia của 1 vài người bị xóa ở trên"

## Symptom

Khi người quản trị cập nhật buổi họp (meeting) và loại bỏ một hoặc nhiều thành viên (participants) khỏi danh sách tham gia, hệ thống vẫn ghi nhận các thành viên đã bị xóa này vắng mặt khi chạy job kiểm tra điểm danh (`CheckMeetingAttendanceUseCase` / `meeting_checker_job`) và tự động tạo vi phạm (violation) phạt vắng họp không phép cho họ.

- **Hành vi thực tế**: Thành viên đã bị xóa khỏi meeting vẫn nhận vi phạm "Vắng sinh hoạt: [Tên meeting] (Không xin phép)".
- **Hành vi kỳ vọng**: Thành viên đã bị xóa khỏi meeting (soft-delete) không còn nằm trong danh sách participants của meeting và không bị tính vắng mặt hay tạo vi phạm.

## Reproduction

1. Tạo một meeting có yêu cầu điểm danh (`require_check_in=True`) với danh sách gồm User A và User B.
2. Cập nhật meeting (`PUT /api/v1/meetings/{id}`), loại bỏ User B ra khỏi danh sách `user_ids` (chỉ giữ lại User A).
3. Chạy use case kiểm tra điểm danh `CheckMeetingAttendanceUseCase.execute(target_date)`.
4. Quan sát: Hệ thống phát tán sự kiện `ParticipantAbsenceRecorded` cho User B và `ViolationHandler` tự động tạo bản ghi Violation phạt User B vì vắng mặt không phép.

## Suspected Code Paths

- `backend/app/meeting/infrastructure/model.py:45` (`Meeting.to_entity`):
  Phương thức `to_entity()` chuyển đổi ORM sang Domain Entity bằng `[p.to_entity() for p in self.participants]`, không lọc bỏ các participant đã bị soft-delete (`p.is_deleted == True`).

- `backend/app/meeting/infrastructure/repository.py:23-46` (`MeetingRepository._to_domain`):
  Phương thức mapping ORM `Meeting` sang Domain `Meeting` lặp qua `for p in orm.participants:` và đưa toàn bộ vào danh sách `DomainMeeting.participants` mà không kiểm tra `if p.is_deleted: continue`.

- `backend/app/meeting/infrastructure/repository.py:173-185` (`MeetingRepository.get_by_date`):
  Query sử dụng `joinedload(ORMMeeting.participants)` tải toàn bộ quan hệ participants (kể cả các bản ghi có `is_deleted == True`). Khi kết hợp với `_to_domain`, các participant bị xóa vẫn xuất hiện trong Domain Entity.

- `backend/app/meeting/infrastructure/repository.py:273-326` (`MeetingRepository.save`):
  Khi cập nhật danh sách participants, repo đánh dấu `old_p.is_deleted = True`. Tuy nhiên sau khi `refresh(orm)`, ORM instance trong session vẫn còn các object con này trong relationship collection và `_to_domain(orm)` trả về entity vẫn chứa các participant đã xóa.

- `backend/app/meeting/application/check_meeting_attendance_use_case.py:52-69`:
  Khi duyệt qua `meeting.participants`, do entity chứa cả participant đã xóa (với `check_in_at is None`), use case phát tán event `ParticipantAbsenceRecorded` cho user đã bị xóa.

- `backend/app/violation/application/event_handlers.py:66-93` (`ViolationHandler._handle_meeting_absence`):
  Khi nhận event vắng, handler cố gắng cập nhật `update_participant_status` (bị lỗi do participant đã soft-delete và bị nuốt warning), sau đó vẫn tiếp tục gọi `create_violation_use_case.execute` tạo vi phạm vắng mặt cho user.

## Root Cause Hypothesis

Khi xóa participant khỏi meeting trong `UpdateMeetingUseCase`, `MeetingRepository.save` thực hiện soft-delete bản ghi bằng cách đặt `is_deleted = True` trên bảng `meeting_participants`. Tuy nhiên, các phương thức mapper (`Meeting.to_entity()` trong `model.py` và `MeetingRepository._to_domain()` trong `repository.py`) cũng như câu lệnh nạp dữ liệu (`get_by_date` dùng `joinedload`) không lọc bỏ các bản ghi `is_deleted == True`. Do đó, Domain Entity `Meeting` vẫn chứa các participant đã bị xóa. Khi `CheckMeetingAttendanceUseCase` chạy kiểm tra điểm danh cuối ngày, nó quét qua toàn bộ `meeting.participants` (bao gồm các participant đã bị xóa với `check_in_at = None`) và bắn event tạo vi phạm vắng họp sai cho các thành viên này.

- **Độ tin cậy (Confidence)**: High (Rất cao - đã xác định chính xác luồng code và nguyên nhân gốc).

## Proposed Remediation

**Preferred**:
1. **Lọc `is_deleted` ở tầng Mapper & Entity**:
   - Trong `backend/app/meeting/infrastructure/model.py` (`Meeting.to_entity`): Lọc chỉ lấy các participant chưa bị xóa: `[p.to_entity() for p in self.participants if not p.is_deleted]`.
   - Trong `backend/app/meeting/infrastructure/repository.py` (`MeetingRepository._to_domain`): Bỏ qua các participant đã xóa (`if getattr(p, "is_deleted", False): continue`).
2. **Cập nhật Query nạp dữ liệu (`get_by_date`)**:
   - Điều chỉnh query trong `MeetingRepository.get_by_date` để chỉ load các `ORMParticipant` có `is_deleted == False` (hoặc dùng `outerjoin` với `contains_eager` có điều kiện `is_deleted.is_(False)` tương tự như `get_with_participants`).
3. **Phòng vệ tại `CheckMeetingAttendanceUseCase` & `ViolationHandler`**:
   - Đảm bảo use case chỉ duyệt active participants.
   - Trong `ViolationHandler._handle_meeting_absence`: Nếu không tìm thấy participant hợp lệ trong meeting (`participant_repo.get_by_meeting_and_user` trả về None hoặc đã bị xóa), bỏ qua việc tạo vi phạm thay vì tiếp tục tạo vi phạm khi bắt được exception.

**Alternatives**:
- Thêm điều kiện lọc trực tiếp vào quan hệ SQLAlchemy: Cấu hình `primaryjoin="and_(Meeting.id==MeetingParticipant.meeting_id, MeetingParticipant.is_deleted.is_(False))"` trên `Meeting.participants`. (Ưu điểm: Tự động lọc ở mọi relationship query; Nhược điểm: Cần quản lý cẩn thận khi thực hiện thao tác restore/tái sử dụng bản ghi soft-deleted).

**Files likely to change**:
- `backend/app/meeting/infrastructure/model.py`
- `backend/app/meeting/infrastructure/repository.py`
- `backend/app/meeting/application/check_meeting_attendance_use_case.py`
- `backend/app/violation/application/event_handlers.py`
- `backend/tests/meeting/test_update_meeting_participants.py` (hoặc test case tương ứng)

**Tests to add or update**:
- Test cập nhật meeting loại bỏ participant: Kiểm tra `meeting.participants` sau khi update không còn chứa user bị xóa.
- Test `CheckMeetingAttendanceUseCase`: Tạo meeting có 1 user active và 1 user bị soft-delete; chạy check attendance và xác nhận chỉ có 1 event được bắn cho user active (nếu chưa check-in), không tạo vi phạm cho user đã bị xóa.

## Risks & Considerations

- **Dữ liệu vi phạm cũ**: Cần kiểm tra xem trong cơ sở dữ liệu hiện tại có vi phạm nào đã bị tạo sai cho các user đã bị xóa khỏi meeting trước đó hay không để có thể dọn dẹp nếu cần.
- **Tương thích với các use case khác**: Cần kiểm tra các nơi sử dụng `meeting.participants` (ví dụ: `calculate_current_capacity_use_case`, `checkout_use_case`, `export`, v.v.) để đảm bảo tính nhất quán sau khi lọc `is_deleted`.

## Open Questions

- *Không có (Đã xác định rõ nguyên nhân và phương án khắc phục).*
