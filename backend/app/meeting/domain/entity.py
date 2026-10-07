from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field

from app.meeting.domain.value_objects import EvaluationType, ParticipantStatus
from app.shared.domain.base_entity import BaseEntity


class UserRef(BaseModel):
    """Tham chiếu danh tính User trong Domain (Value Object snapshot)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str = ""
    avatar_url: str | None = None


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

    def check_in(
        self,
        check_in_time: datetime,
        image_url: str | None = None,
        status: ParticipantStatus = ParticipantStatus.JOINED,
    ):
        """Thực hiện check-in cho thành viên (image_url tùy chọn, ví dụ quẹt thẻ)."""
        if self.status in (
            ParticipantStatus.JOINED,
            ParticipantStatus.LATE_EXCUSED,
            ParticipantStatus.LATE_UNEXCUSED,
            ParticipantStatus.COMPLETED,
        ):
            return True, "Checkin thanh cong"

        self.check_in_at = check_in_time
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
        else:
            self.check_in_at = check_in_at or self.check_in_at or default_start_time
            if new_status == ParticipantStatus.COMPLETED:
                self.check_out_at = (
                    check_out_at or self.check_out_at or default_end_time
                )
            else:
                self.check_out_at = (
                    check_out_at if check_out_at is not None else self.check_out_at
                )


class EvaluationScoreItem(BaseModel):
    """Điểm của từng tiêu chí đánh giá (Value Object)"""

    criteria_code: str
    score: int = Field(ge=1, le=5)


class MeetingEvaluation(BaseEntity):
    """Phiếu đánh giá cá nhân 2 chiều giữa Trainer và Trainee (Domain Entity)"""

    meeting_id: int
    reviewer_id: int
    target_user_id: int
    evaluation_type: EvaluationType
    is_anonymous: bool = False
    scores: list[EvaluationScoreItem] = Field(default_factory=list)
    average_score: float = 0.0
    feedback_text: str | None = None
    reviewer: UserRef | None = None
    target_user: UserRef | None = None

    def calculate_average(self) -> float:
        """Tính điểm trung bình cộng của các tiêu chí."""
        if not self.scores:
            self.average_score = 0.0
            return 0.0
        self.average_score = round(
            sum(s.score for s in self.scores) / len(self.scores), 2
        )
        return self.average_score


class Meeting(BaseEntity):
    """Buổi họp / Lớp học (Domain Entity - Write Aggregate)"""

    title: str
    start_time: datetime
    end_time: datetime
    content: str | None = None
    require_check_in: bool = True
    enable_evaluation: bool = False
    participants: list[MeetingParticipant] = Field(default_factory=list)
    creator: UserRef | None = None

    @property
    def evaluation_deadline(self) -> datetime | None:
        """Hạn chót đánh giá: Single Source of Truth tính động từ end_time + 24h."""
        if not self.enable_evaluation:
            return None
        return self.end_time + timedelta(hours=24)

    def is_evaluation_open(self, current_time: datetime) -> tuple[bool, str]:
        """Kiểm tra điều kiện mở cổng đánh giá 2 chiều (Domain Business Rule)."""
        if not self.enable_evaluation:
            return False, "Buổi học không kích hoạt tính năng đánh giá 2 chiều."
        if current_time < self.start_time:
            return False, "Buổi học chưa bắt đầu, chưa thể gửi đánh giá."
        if self.is_evaluation_expired(current_time):
            return False, "Đã quá thời hạn 24 giờ sau buổi học để gửi đánh giá."
        return True, "Cổng đánh giá đang mở."

    def is_evaluation_expired(self, current_time: datetime) -> bool:
        """Kiểm tra xem buổi học đã quá hạn 24h để đánh giá hay chưa."""
        if not self.enable_evaluation:
            return False
        deadline = self.evaluation_deadline
        return deadline is not None and current_time > deadline

    def is_ongoing(self, current_time: datetime) -> bool:
        """Kiểm tra xem buổi họp có đang diễn ra hay không"""
        return self.start_time <= current_time <= self.end_time

    def is_finished(self, current_time: datetime) -> bool:
        """Kiểm tra xem buổi họp đã kết thúc chưa"""
        return current_time > self.end_time

    def is_late(self, check_in_time: datetime) -> bool:
        """Kiểm tra xem việc check-in có bị trễ hay không"""
        if not self.require_check_in:
            return False
        return check_in_time > (self.start_time + timedelta(minutes=5))


MeetingParticipant.model_rebuild()
EvaluationScoreItem.model_rebuild()
MeetingEvaluation.model_rebuild()
Meeting.model_rebuild()
