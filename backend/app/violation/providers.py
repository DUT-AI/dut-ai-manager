from dishka import Provider, Scope, provide
from sqlmodel import Session
from app.violation.infrastructure.repository import ViolationRepository
from app.violation.application.use_cases import CreateViolationUseCase
from app.violation.permission_handler import PermissionViolationHandler
from app.permission_request.infrastructure.repository import PermissionRequestRepository

class ViolationModuleProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_violation_repo(self, session: Session) -> ViolationRepository:
        return ViolationRepository(session)

    @provide
    def create_violation_uc(self, repo: ViolationRepository) -> CreateViolationUseCase:
        return CreateViolationUseCase(repo)

    @provide
    def get_permission_handler(
        self, create_violation_uc: CreateViolationUseCase, permission_repo: PermissionRequestRepository
    ) -> PermissionViolationHandler:
        return PermissionViolationHandler(create_violation_uc, permission_repo)
