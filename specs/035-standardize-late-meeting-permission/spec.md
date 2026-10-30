# Feature Specification: Chuẩn hóa nghiệp vụ Xin Đi Trễ Buổi Meeting (LATE Permission Request)

**Feature Branch**: `035-standardize-late-meeting-permission`  
**Created**: 2026-10-31  
**Status**: Draft  

## 1. Problem Statement & Thực trạng hiện tại
Hiện tại, đơn xin phép loại đi trễ (`RequestCategory.LATE`) trong `CreatePermissionRequestUseCase`:
- **Chưa có ràng buộc Domain đầy đủ**:
  - Không bắt buộc chọn `meeting_id` (nếu người dùng nộp đơn LATE mà không có `meeting_id` thì đơn trở nên vô nghĩa vì không biết trễ buổi nào).
  - Không bắt buộc nhập giờ dự kiến đến (`start_time`), hoặc nhập `start_time` trước giờ bắt đầu của meeting, hoặc nhập sau giờ kết thúc meeting.
  - Người dùng có thể nộp đơn xin trễ cho một buổi meeting đã kết thúc từ lâu trong quá khứ.
- **Chưa đồng bộ trạng thái Participant trước giờ điểm danh**:
  - Khi nộp đơn `ABSENCE` (xin nghỉ), hệ thống lập tức gọi `repo.mark_participant_excused(meeting_id, user_id)` để cập nhật trạng thái participant sang `ABSENT_EXCUSED`.
  - Nhưng khi nộp đơn `LATE` (xin đi trễ), hệ thống **hoàn toàn không làm gì** với participant. Trạng thái participant vẫn là `NOT_JOINED`. Nếu học viên chưa đến kịp, người quản trị/mentor nhìn vào bảng điểm danh không biết học viên này đã có đơn xin trễ hay chưa.
- **Cơ chế đối soát lúc Điểm danh (`check_in`) và Ghi nhận vi phạm (`violation`)**:
  - Tại `Participant.check_in`: Kiểm tra nếu `self.status == ParticipantStatus.LATE_EXCUSED` thì bảo lưu có phép. Nhưng do khi tạo đơn chưa set `LATE_EXCUSED`, nên nếu học viên điểm danh sau giờ bắt đầu meeting, hệ thống đánh dấu họ là `LATE_UNEXCUSED`.
  - Khi phát sự kiện `ParticipantLateRecorded`, `ViolationHandler._handle_meeting_late` mới đi query ngược lại xem có đơn xin trễ không. Nếu có đơn và `check_in_at <= late_req.start_time` mới sửa lại thành `LATE_EXCUSED`. Cơ chế này chạy vòng vèo, dễ lệch múi giờ (đang dùng `replace(tzinfo=None)`) và thiếu tính nhất quán.

---

## 2. Nghiệp vụ Chuẩn (Standard Domain Rules) cho Xin Đi Trễ (`LATE`)

### Quy tắc 1: Điều kiện hợp lệ khi tạo đơn (Invariants Validation)
1. **Bắt buộc có `meeting_id`**: Phải chọn đúng buổi meeting mà học viên tham gia.
2. **Kiểm tra tư cách tham gia**: Học viên phải có tên trong danh sách `meeting_participants` của buổi họp đó (không thể xin trễ một buổi mình không tham gia).
3. **Bắt buộc có giờ dự kiến đến (`start_time` / `expected_arrival_time`)**:
   - `start_time` phải có đầy đủ ngày và giờ.
   - **Ràng buộc thời gian**:
     $$\text{meeting.start\_time} < \text{start\_time} \le \text{meeting.end\_time}$$
     *(Học viên không thể xin trễ mà giờ đến lại sớm hơn giờ bắt đầu meeting, hoặc muộn hơn lúc meeting đã tan).*
4. **Thời điểm nộp đơn**:
   - Đơn xin đi trễ phải được nộp **trước khi buổi meeting kết thúc** (`now < meeting.end_time`). Không chấp nhận nộp đơn cho buổi họp đã kết thúc.

### Quy tắc 2: Tác động tức thì lên trạng thái lớp học (State Transition)
- Ngay khi đơn xin trễ hợp lệ được tạo:
  - Nếu học viên chưa điểm danh (`status == NOT_JOINED`), hệ thống cập nhật trạng thái participant thành **`LATE_EXCUSED`** (để mentor/quản trị viên nhìn danh sách biết ngay bạn này đã xin phép đi trễ và biết dự kiến mấy giờ đến).
  - Nếu học viên hủy/xóa đơn xin trễ: Nếu chưa điểm danh, khôi phục trạng thái về `NOT_JOINED`.

### Quy tắc 3: Xử lý khi Học viên đến và Điểm danh (Check-in Processing)
Khi học viên quẹt thẻ / điểm danh qua camera tại thời điểm `check_in_at`:
1. **Trường hợp đến ĐÚNG GIỜ (`check_in_at <= meeting.start_time`)**:
   - Dù trước đó có xin đi trễ nhưng thực tế đã đến kịp đúng giờ.
   - Trạng thái được cập nhật thành **`JOINED`** (Điểm danh thành công, không tính trễ).
2. **Trường hợp đến TRỄ NHƯNG TRONG GIỜ ĐÃ XIN PHÉP (`meeting.start_time < check_in_at <= late_req.start_time`)**:
   - Trạng thái là **`LATE_EXCUSED`** (Đi trễ có phép).
   - **Không ghi nhận vi phạm kỷ luật**.
3. **Trường hợp đến TRỄ VƯỢT QUÁ GIỜ ĐÃ XIN PHÉP (`check_in_at > late_req.start_time`)**:
   - Trạng thái chuyển thành **`LATE_UNEXCUSED`** (Đi trễ vượt hạn phép).
   - Hệ thống tự động ghi nhận biên bản vi phạm kỷ luật với lý do: *"Đi trễ vượt quá thời gian xin phép (Dự kiến: HH:mm, Thực tế: HH:mm)"*.
4. **Trường hợp đã xin trễ nhưng KHÔNG ĐẾN HỌP (Hết buổi vẫn không check-in)**:
   - Khi buổi meeting kết thúc hoặc quét định kỳ cuối ngày, nếu học viên vẫn chưa check-in:
   - Chuyển trạng thái sang **`ABSENT_UNEXCUSED`** (vì xin đi trễ chứ không xin nghỉ, mà lại không đến) và ghi nhận vi phạm vắng không phép.

---

## 3. Kiến trúc Triển khai (Target Architecture)

1. **Domain Layer (`PermissionRequest` entity & `MeetingParticipant`)**:
   - Bổ sung phương thức nghiệp vụ: `request.validate_late(meeting: Meeting)`.
   - Chuẩn hóa so sánh thời gian đảm bảo Enterprise UTC.
2. **Use Case Layer (`CreatePermissionRequestUseCase`)**:
   - Inject `MeetingRepository`.
   - Nếu `category == RequestCategory.LATE`:
     - Validate sự tồn tại của meeting và thời gian `start_time`.
     - Gọi `request.validate_late(meeting)`.
     - Lưu đơn.
     - Đánh dấu participant sang `LATE_EXCUSED` nếu chưa check-in.
3. **Use Case Layer (`DeletePermissionRequestUseCase`)**:
   - Nếu xóa đơn `LATE`, revert participant về `NOT_JOINED` nếu chưa check-in.
4. **Attendance & Violation Layer**:
   - Tinh chỉnh `Participant.check_in` và `_handle_meeting_late` để tuân thủ triệt để logic đối soát UTC thời gian dự kiến đến.
