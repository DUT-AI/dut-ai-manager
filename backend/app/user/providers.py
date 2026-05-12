from dishka import Provider, Scope, provide
from sqlmodel import Session

from app.user.application.use_cases import (
    CreateUserUseCase,
    DeleteUserUseCase,
    GetUserUseCase,
    ImportUsersUseCase,
    UpdateAvatarUseCase,
    UpdateUserUseCase,
)
from app.user.infrastructure.repository import UserRepository
from app.user.infrastructure.monthly_stats_repository import MonthlyUserStatsRepository
from app.shared.infrastructure.minio_service import MinioService


class UserModuleProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_user_repo(self, session: Session) -> UserRepository:
        return UserRepository(session)

    @provide
    def get_monthly_stats_repo(self, session: Session) -> MonthlyUserStatsRepository:
        return MonthlyUserStatsRepository(session)

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
        self, create_uc: CreateUserUseCase, repo: UserRepository
    ) -> ImportUsersUseCase:
        return ImportUsersUseCase(create_uc, repo)

    @provide
    def update_avatar_uc(
        self, repo: UserRepository, minio: MinioService
    ) -> UpdateAvatarUseCase:
        return UpdateAvatarUseCase(repo, minio)
