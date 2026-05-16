from dishka import Provider, Scope, provide
from sqlalchemy.orm import Session

from app.rbac.infrastructure.repository import RoleRepository
from app.shared.infrastructure.minio_service import MinioService
from app.user.application.use_cases import (
    CreateUserUseCase,
    DeleteUserUseCase,
    GetUserUseCase,
    ImportUsersUseCase,
    UpdateAvatarUseCase,
    UpdateUserUseCase,
)
from app.user.infrastructure.monthly_stats_repository import MonthlyUserStatsRepository
from app.user.infrastructure.repository import UserRepository


class UserModuleProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_user_repo(self, session: Session) -> UserRepository:
        return UserRepository(session)

    @provide
    def get_monthly_stats_repo(self, session: Session) -> MonthlyUserStatsRepository:
        return MonthlyUserStatsRepository(session)

    @provide
    def get_role_repo(self, session: Session) -> RoleRepository:
        return RoleRepository(session)

    @provide
    def get_user_uc(self, repo: UserRepository) -> GetUserUseCase:
        return GetUserUseCase(repo)

    @provide
    def update_user_uc(self, repo: UserRepository) -> UpdateUserUseCase:
        return UpdateUserUseCase(repo)

    @provide
    def delete_user_uc(self, repo: UserRepository) -> DeleteUserUseCase:
        return DeleteUserUseCase(repo)

    @provide
    def create_user_uc(self, repo: UserRepository) -> CreateUserUseCase:
        return CreateUserUseCase(repo)

    @provide
    def import_users_uc(
        self,
        create_uc: CreateUserUseCase,
        user_repo: UserRepository,
        role_repo: RoleRepository,
    ) -> ImportUsersUseCase:
        return ImportUsersUseCase(create_uc, user_repo, role_repo)

    @provide
    def update_avatar_uc(
        self, repo: UserRepository, minio: MinioService
    ) -> UpdateAvatarUseCase:
        return UpdateAvatarUseCase(repo, minio)
