from dishka import Provider, Scope, provide
from sqlmodel import Session
from app.permission_request.infrastructure.repository import PermissionRequestRepository

class PermissionRequestModuleProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_permission_repo(self, session: Session) -> PermissionRequestRepository:
        return PermissionRequestRepository(session)
