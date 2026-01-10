from app.core.permissions import UserPermission
from app.core.deps import hasPermission
from app.core.config import settings
from app.core.deps import CurrentUser
from app.core.deps import ServiceFactoryDI
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
    ChangePasswordRequest,
)
from app.schemas.response import ApiResponse
from fastapi import APIRouter, Response

router = APIRouter(prefix="/auth", tags=["auth"])


# Endpoints
@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(
    request: LoginRequest,
    response: Response,
    service_factory: ServiceFactoryDI,
):
    """Login with email and password."""
    user = service_factory.auth.authenticate(request.email, request.password)

    # Create tokens
    access_token, rf_token = service_factory.auth.create_tokens(user.id)

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

    return ApiResponse.success(
        data=TokenResponse(access_token=access_token, refresh_token=rf_token),
        message="Login successful",
    )


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
async def refresh_token(
    request: RefreshTokenRequest,
    response: Response,
    service_factory: ServiceFactoryDI,
):
    """Refresh access token using refresh token."""
    tokens = service_factory.auth.refresh_tokens(request.refresh_token)

    access_token, new_refresh_token = tokens

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
        data=TokenResponse(access_token=access_token, refresh_token=new_refresh_token),
    )


@router.post("/logout", response_model=ApiResponse[None])
async def logout(response: Response):
    """Logout by clearing cookies."""
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return ApiResponse.success(message="Successfully logged out")


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_me(current_user: CurrentUser):
    """Get current user info."""
    return ApiResponse.success(
        data=UserResponse.model_validate(current_user),
    )


@router.post(
    "/change-password",
    response_model=ApiResponse[None],
    dependencies=[hasPermission(UserPermission.UPDATE)],
)
async def change_password(
    request: ChangePasswordRequest,
    current_user: CurrentUser,
    service_factory: ServiceFactoryDI,
):
    """Change user password"""
    service_factory.auth.change_password(
        current_user.id, request.old_password, request.new_password
    )

    return ApiResponse.success(message="Password changed successfully")
