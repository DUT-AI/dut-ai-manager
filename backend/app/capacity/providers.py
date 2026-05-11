from dishka import Provider, Scope, provide
from app.capacity.application.service import CapacityService
from app.meeting.infrastructure.repository import MeetingRepository


class CapacityProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_capacity_service(
        self,
        meeting_repo: MeetingRepository,
    ) -> CapacityService:
        return CapacityService(meeting_repo)
