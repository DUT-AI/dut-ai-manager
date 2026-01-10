# app/core/factories/repository_factory.py
from app.api.v1.repositories.homework_repository import HomeworkRepository
from app.api.v1.repositories.homework_submission_repository import (
    HomeworkSubmissionRepository,
)
from app.api.v1.repositories.team_repository import TeamRepository
from app.api.v1.repositories import (
    AccountRepository,
    BonusPointRepository,
    PermissionRepository,
    PermissionRequestRepository,
    RolePermissionRepository,
    RoleRepository,
    UserRepository,
    ViolationRepository,
)
from sqlmodel import Session


class RepositoryFactory:
    """Factory để tạo các Repository."""

    def __init__(self, session: Session):
        self._session = session
        self._cache: dict = {}

    @property
    def user(self) -> UserRepository:
        if "user" not in self._cache:
            self._cache["user"] = UserRepository(self._session)
        return self._cache["user"]

    @property
    def account(self) -> AccountRepository:
        if "account" not in self._cache:
            self._cache["account"] = AccountRepository(self._session)
        return self._cache["account"]

    @property
    def role(self) -> RoleRepository:
        if "role" not in self._cache:
            self._cache["role"] = RoleRepository(self._session)
        return self._cache["role"]

    @property
    def permission(self) -> PermissionRepository:
        if "permission" not in self._cache:
            self._cache["permission"] = PermissionRepository(self._session)
        return self._cache["permission"]

    @property
    def role_permission(self) -> RolePermissionRepository:
        if "role_permission" not in self._cache:
            self._cache["role_permission"] = RolePermissionRepository(self._session)
        return self._cache["role_permission"]

    @property
    def permission_request(self) -> PermissionRequestRepository:
        if "permission_request" not in self._cache:
            self._cache["permission_request"] = PermissionRequestRepository(
                self._session
            )
        return self._cache["permission_request"]

    @property
    def bonus_point(self) -> BonusPointRepository:
        if "bonus_point" not in self._cache:
            self._cache["bonus_point"] = BonusPointRepository(self._session)
        return self._cache["bonus_point"]

    @property
    def violation(self) -> ViolationRepository:
        if "violation" not in self._cache:
            self._cache["violation"] = ViolationRepository(self._session)
        return self._cache["violation"]

    @property
    def team(self) -> TeamRepository:
        if "team" not in self._cache:
            self._cache["team"] = TeamRepository(self._session)
        return self._cache["team"]

    @property
    def homework(self) -> HomeworkRepository:
        if "homework" not in self._cache:
            self._cache["homework"] = HomeworkRepository(self._session)
        return self._cache["homework"]

    @property
    def homework_submission(self) -> HomeworkSubmissionRepository:
        if "homework_submission" not in self._cache:
            self._cache["homework_submission"] = HomeworkSubmissionRepository(
                self._session
            )
        return self._cache["homework_submission"]
