from app.meeting.infrastructure.repository import MeetingRepository


class DeleteMeetingUseCase:
    """Xóa một buổi họp (Soft-delete)"""

    def __init__(self, repo: MeetingRepository):
        self.repo = repo

    def execute(self, meeting_id: int) -> bool:
        return self.repo.delete(meeting_id)
