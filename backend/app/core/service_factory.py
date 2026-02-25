from app.api.v1.services.auth_service import AuthService
from app.api.v1.services.bonus_point_service import BonusPointService
from app.api.v1.services.homework_service import HomeworkService
from app.api.v1.services.homework_submission import HomeworkSubmissionService
from app.api.v1.services.meeting_service import MeetingService
from app.api.v1.services.notification_service import NotificationService
from app.api.v1.services.permission_request_service import PermissionRequestService
from app.api.v1.services.report_service import ReportService
from app.api.v1.services.role_permission_service import RolePermissionService
from app.api.v1.services.team_service import TeamService
from app.api.v1.services.user_service import UserService
from app.api.v1.services.violation_service import ViolationService
from app.core.minio_service import MinioService
from app.core.repository_factory import RepositoryFactory
from app.api.v1.services.role_api_key_service import RoleApiKeyService
from app.core.discord_service import DiscordService
from app.api.v1.services.zalo_service import ZaloService
from app.api.v1.services.zalo_bot_service import ZaloBotService
from app.api.v1.services.email_service import EmailService


class ServiceFactory:
    """Factory để tạo các Service."""

    def __init__(
        self,
        repo_factory: RepositoryFactory,
        minio_service: MinioService,
        discord_service: DiscordService,
        email_service: EmailService,
    ):
        self._repo = repo_factory
        self._minio_service = minio_service
        self._discord_service = discord_service
        self._email_service = email_service
        self._cache: dict = {}

    @property
    def auth(self) -> AuthService:
        if "auth" not in self._cache:
            self._cache["auth"] = AuthService(self._repo.user, self._repo.account)
        return self._cache["auth"]

    @property
    def minio(self) -> MinioService:
        return self._minio_service

    @property
    def user(self) -> UserService:
        if "user" not in self._cache:
            self._cache["user"] = UserService(
                user_repo=self._repo.user,
                role_repo=self._repo.role,
                auth_service=self.auth,
                minio_service=self.minio,
                email_service=self._email_service,
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
                self._repo.permission_request,
                violation_service=self.violation,
                notification_service=self.notification,
            )
        return self._cache["permission_request"]

    @property
    def zalo(self) -> ZaloService:
        if "zalo" not in self._cache:
            self._cache["zalo"] = ZaloService()
        return self._cache["zalo"]

    @property
    def zalo_bot(self) -> ZaloBotService:
        if "zalo_bot" not in self._cache:
            self._cache["zalo_bot"] = ZaloBotService(user_service=self.user)
        return self._cache["zalo_bot"]

    @property
    def notification(self) -> NotificationService:
        if "notification" not in self._cache:
            self._cache["notification"] = NotificationService(
                discord_service=self._discord_service,
                zalo_service=self.zalo,
                zalo_bot_service=self.zalo_bot,
            )
        return self._cache["notification"]

    @property
    def bonus_point(self) -> BonusPointService:
        if "bonus_point" not in self._cache:
            self._cache["bonus_point"] = BonusPointService(self._repo.bonus_point)
        return self._cache["bonus_point"]

    @property
    def violation(self) -> ViolationService:
        if "violation" not in self._cache:
            self._cache["violation"] = ViolationService(
                self._repo.violation,
                user_service=self.user,
                notification_service=self.notification,
            )
        return self._cache["violation"]

    @property
    def team(self) -> TeamService:
        if "team" not in self._cache:
            self._cache["team"] = TeamService(self._repo.team)
        return self._cache["team"]

    @property
    def homework(self) -> HomeworkService:
        if "homework" not in self._cache:
            self._cache["homework"] = HomeworkService(
                self._repo,
                notification_service=self.notification,
                minio_service=self.minio,
            )
        return self._cache["homework"]

    @property
    def homework_submission(self) -> HomeworkSubmissionService:
        if "homework_submission" not in self._cache:
            self._cache["homework_submission"] = HomeworkSubmissionService(
                self._repo,
                violation_service=self.violation,
                user_service=self.user,
                minio_service=self.minio,
            )
        return self._cache["homework_submission"]

    @property
    def report(self) -> ReportService:
        if "report" not in self._cache:
            self._cache["report"] = ReportService(
                bonus_point_service=self.bonus_point,
                violation_service=self.violation,
                permission_request_service=self.permission_request,
                meeting_service=self.meeting,
                homework_submission_service=self.homework_submission,
            )
        return self._cache["report"]

    @property
    def meeting(self) -> MeetingService:
        if "meeting" not in self._cache:
            self._cache["meeting"] = MeetingService(
                repo_factory=self._repo,
                meeting_repo=self._repo.meeting,
                participant_repo=self._repo.meeting_participant,
                user_service=self.user,
                violation_service=self.violation,
                minio_service=self.minio,
                notification_service=self.notification,
            )
        return self._cache["meeting"]

    @property
    def role_api_key(self) -> RoleApiKeyService:
        if "role_api_key" not in self._cache:
            self._cache["role_api_key"] = RoleApiKeyService(
                self._repo.role_api_key, self._repo.role
            )
        return self._cache["role_api_key"]
