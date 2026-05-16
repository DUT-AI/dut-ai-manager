"""
Auth Web Controller — API routes for authentication.
"""

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Cookie, Response
from loguru import logger

from app.auth.application.dtos import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserReponseMe,
)
from app.auth.application.use_cases import (
    AuthenticateUseCase,
    ChangePasswordUseCase,
    RefreshTokenUseCase,
)
from app.core.config import settings
from app.core.deps import CurrentUser
from app.shared.application.response import ApiResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=ApiResponse[TokenResponse])
@inject
async def login(
    request: LoginRequest,
    response: Response,
    uc: FromDishka[AuthenticateUseCase],
):
    """Authenticate user and return tokens."""
    user, access_token, rf_token = uc.execute(request.email, request.password)

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
        value=rf_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )

    token_data = TokenResponse(access_token=access_token, refresh_token=rf_token)

    return ApiResponse.success(
        data=token_data,
        message="Login successful",
    )


@router.post("/refresh", response_model=ApiResponse)
@inject
async def refresh_token(
    response: Response,
    uc: FromDishka[RefreshTokenUseCase],
    request_data: RefreshTokenRequest | None = None,
    refresh_token_cookie: str | None = Cookie(None, alias="refresh_token"),
):
    """Refresh tokens with a valid refresh token."""
    token = None
    if request_data and request_data.refresh_token:
        token = request_data.refresh_token
    else:
        token = refresh_token_cookie

    if not token:
        return ApiResponse.error(message="Refresh token is missing")

    access_token, new_refresh_token = uc.execute(token)

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


@router.get("/me", response_model=ApiResponse[UserReponseMe])
async def get_me(current_user: CurrentUser):
    """Get current user info using JWT claims."""
    logger.debug(f"Current user: {current_user}")
    return ApiResponse.success(
        data=current_user,
        message="Success fetching current user data",
    )


@router.post("/change-password", response_model=ApiResponse)
@inject
async def change_password(
    request: ChangePasswordRequest,
    current_user: CurrentUser,
    uc: FromDishka[ChangePasswordUseCase],
):
    """Change user password."""
    if request.new_password != request.confirm_password:
        return ApiResponse.error(
            message="Mật khẩu xác nhận không khớp",
            data=None,
        )

    uc.execute(current_user, request.old_password, request.new_password)

    return ApiResponse.success(message="Đổi mật khẩu thành công", data=None)


@router.post("/logout", response_model=ApiResponse)
async def logout(response: Response):
    """Logout by clearing cookies."""
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return ApiResponse.success(message="Successfully logged out", data=None)
