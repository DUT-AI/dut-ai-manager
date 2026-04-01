"""
User Module Dependencies — DI for Use Cases and Repositories.
"""

from typing import Annotated

from app.api.v1.services.email_service import EmailService
from app.auth.application.use_cases import CreateAccountUseCase
from app.auth.deps import create_account_uc as get_create_account_uc
from app.core.database import get_session
from app.shared.infrastructure.minio_service import MinioService
from app.user.application.use_cases import (CreateUserUseCase,
                                            DeleteUserUseCase, GetUserUseCase,
                                            ImportUsersUseCase,
                                            UpdateAvatarUseCase,
                                            UpdateUserUseCase)
from app.user.infrastructure.repository import UserRepository
from fastapi import Depends
from sqlmodel import Session


def get_email_service() -> EmailService:
    return EmailService()


def get_minio_service() -> MinioService:
    return MinioService()


def get_user_repo(session: Session = Depends(get_session)) -> UserRepository:
    return UserRepository(session)


# Use Cases


def get_user_uc(repo: UserRepository = Depends(get_user_repo)) -> GetUserUseCase:
    return GetUserUseCase(repo)


def update_user_uc(repo: UserRepository = Depends(get_user_repo)) -> UpdateUserUseCase:
    return UpdateUserUseCase(repo)


def delete_user_uc(repo: UserRepository = Depends(get_user_repo)) -> DeleteUserUseCase:
    return DeleteUserUseCase(repo)


def create_user_uc(
    repo: UserRepository = Depends(get_user_repo),
    create_account: CreateAccountUseCase = Depends(get_create_account_uc),
    email_service: EmailService = Depends(get_email_service),
) -> CreateUserUseCase:
    return CreateUserUseCase(repo, create_account, email_service)


def import_users_uc(
    create_uc: CreateUserUseCase = Depends(create_user_uc),
    repo: UserRepository = Depends(get_user_repo),
) -> ImportUsersUseCase:
    return ImportUsersUseCase(create_uc, repo)


def update_avatar_uc(
    repo: UserRepository = Depends(get_user_repo),
    minio: MinioService = Depends(get_minio_service),
) -> UpdateAvatarUseCase:
    return UpdateAvatarUseCase(repo, minio)
