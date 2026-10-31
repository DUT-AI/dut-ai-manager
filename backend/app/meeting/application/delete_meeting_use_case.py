from app.meeting.infrastructure.repository import MeetingRepository
from app.shared.application.response import BadRequestException


class DeleteMeetingUseCase:
    """Xóa một buổi họp (Soft-delete)"""

    def __init__(self, repo: MeetingRepository):
        self.repo = repo

    def execute(self, meeting_id: int) -> bool:
        meeting = self.repo.get_by_id(meeting_id)
        if not meeting:
            raise BadRequestException("Không tìm thấy buổi học", status_code=404)
        return self.repo.delete(meeting_id)
