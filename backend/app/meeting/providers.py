from dishka import Provider, Scope, provide
from sqlmodel import Session
from app.meeting.infrastructure.repository import MeetingRepository

class MeetingModuleProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_meeting_repo(self, session: Session) -> MeetingRepository:
        return MeetingRepository(session)
