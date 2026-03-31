from unittest.mock import AsyncMock, MagicMock

import pytest
from app.auth.application.dtos import LoginRequestDTO, UserAuthContextDTO
from app.auth.application.use_cases.login import LoginUseCase
from app.auth.domain.exceptions import (InvalidCredentialsException,
                                        UserInactiveException)


@pytest.fixture
def mock_hasher():
    return MagicMock()


@pytest.fixture
def mock_token_service():
    return MagicMock()


@pytest.fixture
def mock_auth_query():
    return AsyncMock()


@pytest.fixture
def login_use_case(mock_hasher, mock_token_service, mock_auth_query):
    return LoginUseCase(mock_hasher, mock_token_service, mock_auth_query)


@pytest.mark.asyncio
async def test_login_success(
    login_use_case, mock_hasher, mock_token_service, mock_auth_query
):
    # Setup
    email = "test@example.com"
    password = "password"
    user_auth = UserAuthContextDTO(
        id=1,
        email=email,
        hashed_password="hashed_password",
        is_active=True,
        name="Test User",
        avatar_url="avatar.png",
        role_name="admin",
        permissions=["read", "write"],
    )

    mock_auth_query.get_user_auth_context_by_email.return_value = user_auth
    mock_hasher.verify.return_value = True
    mock_token_service.create_access_token.return_value = "access_token"
    mock_token_service.create_refresh_token.return_value = "refresh_token"

    payload = LoginRequestDTO(email=email, password=password)

    # Execute
    result = await login_use_case.execute(payload)

    # Assert
    assert result.access_token == "access_token"
    assert result.refresh_token == "refresh_token"
    mock_auth_query.get_user_auth_context_by_email.assert_called_once_with(email)


@pytest.mark.asyncio
async def test_login_invalid_password(login_use_case, mock_hasher, mock_auth_query):
    # Setup
    email = "test@example.com"
    user_auth = UserAuthContextDTO(
        id=1,
        email=email,
        hashed_password="hashed_password",
        is_active=True,
        name="Test User",
        avatar_url="avatar.png",
        role_name="admin",
        permissions=[],
    )

    mock_auth_query.get_user_auth_context_by_email.return_value = user_auth
    mock_hasher.verify.return_value = False

    payload = LoginRequestDTO(email=email, password="wrongpassword")

    # Execute & Assert
    with pytest.raises(InvalidCredentialsException):
        await login_use_case.execute(payload)


@pytest.mark.asyncio
async def test_login_inactive_user(login_use_case, mock_hasher, mock_auth_query):
    # Setup
    email = "inactive@example.com"
    user_auth = UserAuthContextDTO(
        id=1,
        email=email,
        hashed_password="hashed_password",
        is_active=False,
        name="Test User",
        avatar_url="avatar.png",
        role_name="admin",
        permissions=[],
    )

    mock_auth_query.get_user_auth_context_by_email.return_value = user_auth
    mock_hasher.verify.return_value = True

    payload = LoginRequestDTO(email=email, password="password")

    # Execute & Assert
    with pytest.raises(UserInactiveException):
        await login_use_case.execute(payload)
