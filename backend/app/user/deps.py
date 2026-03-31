"""
User Module Dependencies — DI for Use Cases and Repositories.
"""

from typing import Annotated
from fastapi import Depends
from sqlmodel import Session

from app.core.database import get_session
from app.user.infrastructure.repository import UserRepository
from app.user.application.use_cases import (
    GetUserUseCase,
    UpdateUserUseCase,
    DeleteUserUseCase,
    CreateUserUseCase,
    ImportUsersUseCase,
    UpdateAvatarUseCase
)

# External Services
from app.api.v1.services.auth_service import AuthService
from app.api.v1.services.email_service import EmailService
from app.core.minio_service import MinioService

def get_auth_service(session: Session = Depends(get_session)) -> AuthService:
    return AuthService(session)

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
    auth_service: AuthService = Depends(get_auth_service),
    email_service: EmailService = Depends(get_email_service)
) -> CreateUserUseCase:
    return CreateUserUseCase(repo, auth_service, email_service)

def import_users_uc(
    create_uc: CreateUserUseCase = Depends(create_user_uc),
    repo: UserRepository = Depends(get_user_repo)
) -> ImportUsersUseCase:
    return ImportUsersUseCase(create_uc, repo)

def update_avatar_uc(
    repo: UserRepository = Depends(get_user_repo),
    minio: MinioService = Depends(get_minio_service)
) -> UpdateAvatarUseCase:
    return UpdateAvatarUseCase(repo, minio)
