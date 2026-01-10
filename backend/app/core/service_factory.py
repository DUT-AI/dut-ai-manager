from app.api.v1.services.homework_submission import HomeworkSubmissionService
from app.api.v1.services.auth_service import AuthService
from app.api.v1.services.bonus_point_service import BonusPointService
from app.api.v1.services.permission_request_service import PermissionRequestService
from app.api.v1.services.role_permission_service import RolePermissionService
from app.api.v1.services.user_service import UserService
from app.api.v1.services.violation_service import ViolationService
from app.api.v1.services.team_service import TeamService
from app.api.v1.services.homework_service import HomeworkService
from app.api.v1.services.report_service import ReportService
from app.core.repository_factory import RepositoryFactory


class ServiceFactory:
    """Factory để tạo các Service."""

    def __init__(self, repo_factory: RepositoryFactory):
        self._repo = repo_factory
        self._cache: dict = {}

    @property
    def auth(self) -> AuthService:
        if "auth" not in self._cache:
            self._cache["auth"] = AuthService(self._repo.user, self._repo.account)
        return self._cache["auth"]

    @property
    def user(self) -> UserService:
        if "user" not in self._cache:
            self._cache["user"] = UserService(
                user_repo=self._repo.user, auth_service=self.auth
            )
        return self._cache["user"]

    @property
    def role_permission(self) -> RolePermissionService:
        if "role_permission" not in self._cache:
            self._cache["role_permission"] = RolePermissionService(
                self._repo.role, self._repo.permission, self._repo.role_permission
            )
        return self._cache["role_permission"]

    @property
    def permission_request(self) -> PermissionRequestService:
        if "permission_request" not in self._cache:
            self._cache["permission_request"] = PermissionRequestService(
                self._repo.permission_request
            )
        return self._cache["permission_request"]

    @property
    def bonus_point(self) -> BonusPointService:
        if "bonus_point" not in self._cache:
            self._cache["bonus_point"] = BonusPointService(self._repo.bonus_point)
        return self._cache["bonus_point"]

    @property
    def violation(self) -> ViolationService:
        if "violation" not in self._cache:
            self._cache["violation"] = ViolationService(self._repo.violation)
        return self._cache["violation"]

    @property
    def team(self) -> TeamService:
        if "team" not in self._cache:
            self._cache["team"] = TeamService(self._repo.team)
        return self._cache["team"]

    @property
    def homework(self) -> HomeworkService:
        if "homework" not in self._cache:
            self._cache["homework"] = HomeworkService(self._repo)
        return self._cache["homework"]

    @property
    def homework_submission(self) -> HomeworkSubmissionService:
        if "homework_submission" not in self._cache:
            self._cache["homework_submission"] = HomeworkSubmissionService(
                self._repo, violation_service=self.violation
            )
        return self._cache["homework_submission"]

    @property
    def report(self) -> ReportService:
        if "report" not in self._cache:
            self._cache["report"] = ReportService(
                bonus_point_service=self.bonus_point,
                violation_service=self.violation,
                permission_request_service=self.permission_request,
            )
        return self._cache["report"]
