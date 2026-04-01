"""
Auth Dependencies — DI for Auth Use Cases.
"""

from typing import Annotated

from app.auth.application.use_cases import (AuthenticateUseCase,
                                            ChangePasswordUseCase,
                                            CreateAccountUseCase,
                                            RefreshTokenUseCase,
                                            VerifyTokenUseCase)
from app.auth.infrastructure.repository import AccountRepository
from app.core.database import get_session
from app.user.infrastructure.repository import UserRepository
from fastapi import Depends
from sqlmodel import Session


def get_account_repo(session: Session = Depends(get_session)) -> AccountRepository:
    return AccountRepository(session)


def get_user_repo(session: Session = Depends(get_session)) -> UserRepository:
    return UserRepository(session)


def authenticate_uc(
    account_repo: AccountRepository = Depends(get_account_repo),
    user_repo: UserRepository = Depends(get_user_repo),
) -> AuthenticateUseCase:
    return AuthenticateUseCase(account_repo, user_repo)


def refresh_token_uc(
    account_repo: AccountRepository = Depends(get_account_repo),
    user_repo: UserRepository = Depends(get_user_repo),
) -> RefreshTokenUseCase:
    return RefreshTokenUseCase(account_repo, user_repo)


def verify_token_uc(
    account_repo: AccountRepository = Depends(get_account_repo),
    user_repo: UserRepository = Depends(get_user_repo),
) -> VerifyTokenUseCase:
    return VerifyTokenUseCase(account_repo, user_repo)


def change_password_uc(
    account_repo: AccountRepository = Depends(get_account_repo),
    user_repo: UserRepository = Depends(get_user_repo),
) -> ChangePasswordUseCase:
    return ChangePasswordUseCase(account_repo, user_repo)


def create_account_uc(
    account_repo: AccountRepository = Depends(get_account_repo),
) -> CreateAccountUseCase:
    return CreateAccountUseCase(account_repo)
