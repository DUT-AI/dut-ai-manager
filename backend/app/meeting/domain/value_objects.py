from enum import Enum


class ParticipantStatus(str, Enum):
    """Trạng thái tham dự buổi họp"""

    NOT_JOINED = "chưa tham gia"
    JOINED = "đã checkin"
    COMPLETED = "đã checkout"
