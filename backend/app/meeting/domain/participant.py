from datetime import datetime

from app.meeting.domain.value_objects import ParticipantStatus, UserRef
from app.shared.domain.base_entity import BaseEntity
from app.shared.domain.datetime_types import ensure_utc


class MeetingParticipant(BaseEntity):
    """Thành viên tham gia buổi họp (Domain Entity)"""

    user_id: int
    meeting_id: int | None = None
    check_in_at: datetime | None = None
    check_out_at: datetime | None = None
    status: ParticipantStatus = ParticipantStatus.NOT_JOINED
    link_image: str | None = None
    client_event_id: str | None = None
    user: UserRef | None = None

    def record_check_in(
        self,
        check_in_time: datetime,
        meeting_start_time: datetime,
        image_url: str | None = None,
        client_event_id: str | None = None,
    ) -> tuple[bool, str, bool]:
        """
        Ghi nhận điểm danh cho thành viên theo chuẩn Domain-Driven Design Invariants.

        Quy tắc nghiệp vụ:
        1. Nếu đã COMPLETED -> Từ chối ghi nhận điểm danh đè.
        2. Xác định is_late: check_in_time > meeting_start_time.
        3. Xác định trạng thái:
           - Nếu là LATE_EXCUSED (đã duyệt đơn) -> Bảo lưu LATE_EXCUSED.
           - Nếu là JOINED hoặc LATE_UNEXCUSED -> Giữ nguyên trạng thái.
           - Nếu là NOT_JOINED:
             - is_late == True  -> LATE_UNEXCUSED.
             - is_late == False -> JOINED.
        4. Ghi nhận mốc thời gian check_in_at:
           - Nếu chưa có -> Gán check_in_time (đảm bảo UTC).
           - Nếu đã có -> Giữ mốc ban đầu để bảo vệ dữ liệu gốc.
        5. Cập nhật link_image và client_event_id (nếu được cung cấp).

        Returns:
            tuple[bool, str, bool]: (success, message, is_late)
        """
        check_in_time_utc = ensure_utc(check_in_time)
        meeting_start_time_utc = ensure_utc(meeting_start_time)

        if self.status == ParticipantStatus.COMPLETED:
            return (
                False,
                "Thành viên đã hoàn thành buổi họp, không thể điểm danh lại",
                False,
            )

        is_late = check_in_time_utc > meeting_start_time_utc

        if not is_late:
            # Học viên đến đúng giờ: thực tế đến đúng giờ -> JOINED
            self.status = ParticipantStatus.JOINED
        elif self.status == ParticipantStatus.LATE_EXCUSED:
            # Đến trễ nhưng đã có đơn xin trễ duyệt trước đó -> Bảo lưu
            pass
        elif self.status in (
            ParticipantStatus.JOINED,
            ParticipantStatus.LATE_UNEXCUSED,
        ):
            # Đã điểm danh trước đó, giữ nguyên trạng thái
            pass
        else:
            self.status = ParticipantStatus.LATE_UNEXCUSED

        if self.check_in_at is None:
            self.check_in_at = check_in_time_utc

        if image_url:
            self.link_image = image_url

        if client_event_id:
            self.client_event_id = client_event_id

        msg = "Điểm danh thành công (đi trễ)" if is_late else "Điểm danh thành công"
        return True, msg, is_late

    def check_in(
        self,
        check_in_time: datetime,
        image_url: str | None = None,
        status: ParticipantStatus = ParticipantStatus.JOINED,
    ):
        """Thực hiện check-in cho thành viên (image_url tùy chọn, ví dụ quẹt thẻ)."""
        if self.status == ParticipantStatus.COMPLETED:
            return False, "Da checkout"

        if self.check_in_at is None:
            self.check_in_at = ensure_utc(check_in_time)
        self.status = status
        if image_url:
            self.link_image = image_url
        return True, "Checkin thanh cong"

    def check_out(self, check_out_time: datetime):
        """Thực hiện check-out cho thành viên."""
        if self.status == ParticipantStatus.COMPLETED:
            return True, "Da checkout"

        self.check_out_at = check_out_time
        self.status = ParticipantStatus.COMPLETED
        return True, "Checkout thanh cong"

    def update_attendance_status(
        self,
        new_status: ParticipantStatus,
        check_in_at: datetime | None = None,
        check_out_at: datetime | None = None,
        default_start_time: datetime | None = None,
        default_end_time: datetime | None = None,
    ):
        """Logic nghiệp vụ Domain xử lý cập nhật trạng thái điểm danh thủ công."""
        self.status = new_status
        if new_status in (
            ParticipantStatus.NOT_JOINED,
            ParticipantStatus.ABSENT_EXCUSED,
            ParticipantStatus.ABSENT_UNEXCUSED,
        ):
            self.check_in_at = check_in_at
            self.check_out_at = check_out_at
            if new_status == ParticipantStatus.NOT_JOINED:
                self.link_image = None
        elif new_status == ParticipantStatus.JOINED:
            # Đúng giờ: Ưu tiên check_in_at nếu có, để trống thì gán meeting.start_time
            self.check_in_at = check_in_at or default_start_time
            self.check_out_at = (
                check_out_at if check_out_at is not None else self.check_out_at
            )
        elif new_status in (
            ParticipantStatus.LATE_EXCUSED,
            ParticipantStatus.LATE_UNEXCUSED,
        ):
            # Đi trễ: Ưu tiên check_in_at, để trống thì giữ mốc cũ hoặc gán now
            self.check_in_at = check_in_at or self.check_in_at or default_start_time
            self.check_out_at = (
                check_out_at if check_out_at is not None else self.check_out_at
            )
        else:  # COMPLETED
            self.check_in_at = check_in_at or self.check_in_at or default_start_time
            self.check_out_at = check_out_at or self.check_out_at or default_end_time


MeetingParticipant.model_rebuild()

__all__ = ["MeetingParticipant"]
