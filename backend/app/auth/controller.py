"""
Auth Web Controller — API routes for authentication.
"""

from typing import Annotated
from loguru import logger
from app.auth.application.use_cases import (
    AuthenticateUseCase,
    ChangePasswordUseCase,
    RefreshTokenUseCase,
)
from app.auth.deps import authenticate_uc, change_password_uc, refresh_token_uc
from app.core.config import settings
from app.core.deps import CurrentUser
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.response import ApiResponse
from fastapi import APIRouter, Depends, Response

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(
    request: LoginRequest,
    response: Response,
    uc: Annotated[AuthenticateUseCase, Depends(authenticate_uc)],
):
    """Authenticate user and return tokens."""
    user, access_token, refresh_token = uc.execute(request.email, request.password)

    # Set cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )

    token_data = TokenResponse(access_token=access_token, refresh_token=refresh_token)

    return ApiResponse.success(
        data=token_data,
        message="Login successful",
    )


@router.post("/refresh", response_model=ApiResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    response: Response,
    uc: Annotated[RefreshTokenUseCase, Depends(refresh_token_uc)],
):
    """Refresh tokens with a valid refresh token."""
    access_token, new_refresh_token = uc.execute(request.refresh_token)

    # Set cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )

    return ApiResponse.success(
        data=TokenResponse(access_token=access_token, refresh_token=new_refresh_token)
    )


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_me(current_user: CurrentUser):
    """Get current user info using JWT claims."""
    logger.debug(f"Current user: {current_user}")
    return ApiResponse.success(
        data=UserResponse.model_validate(current_user),
        message="Success fetching current user data",
    )


@router.post("/change-password", response_model=ApiResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: CurrentUser,
    uc: Annotated[ChangePasswordUseCase, Depends(change_password_uc)],
):
    """Change user password."""
    if request.new_password != request.confirm_password:
        return ApiResponse.error(
            message="Mật khẩu xác nhận không khớp",
            data=None,
        )

    uc.execute(current_user, request.old_password, request.new_password)

    return ApiResponse(message="Đổi mật khẩu thành công", data=None)


@router.post("/logout", response_model=ApiResponse)
async def logout(response: Response):
    """Logout by clearing cookies."""
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return ApiResponse(message="Successfully logged out")
