from enum import Enum
from typing import Annotated

from app.core.context import set_current_user_id
from app.core.database import get_session
from app.rbac.domain.entity import RoleType
from app.rbac.infrastructure.repository import RoleApiKeyRepository, RoleRepository
from app.schemas.response import BadRequestException
from app.user.domain.entity import UserEntity
from app.user.infrastructure.repository import UserRepository
from app.utils.password import decode_access_token, verify_password
from fastapi import Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

security = HTTPBearer(auto_error=False)


def get_token_from_cookie_or_header(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> str:
    """Get token from cookie or Authorization header"""
    # Try to get from cookie first
    token = request.cookies.get("access_token")

    # If not in cookie, try Authorization header
    if not token and credentials:
        token = credentials.credentials

    if not token:
        raise BadRequestException(
            status_code=status.HTTP_401_UNAUTHORIZED, message="Not token"
        )

    return token


def get_current_user(
    token: Annotated[str, Depends(get_token_from_cookie_or_header)],
    session: Annotated[Session, Depends(get_session)],
) -> UserEntity:
    """
    Get current user from token.
    Supports:
    1. JWT Access Token (User login)
    2. API Key (Role-based system access)
    """
    # 1. Check for API Key format (sk-...)
    if token.startswith("sk-"):
        role_api_key = RoleApiKeyRepository(session)

        prefix = token[:6] 
        candidates = role_api_key.get_candidates_by_prefix(prefix)

        matched_key = None
        for key in candidates:
            if verify_password(token, key.key_hash):
                matched_key = key
                break

        if not matched_key:
            raise BadRequestException("Invalid API Key", status.HTTP_401_UNAUTHORIZED)

        role = matched_key.role

        system_user = UserEntity(
            id=0,
            name=f"System: {matched_key.name}",
            email=f"system+{matched_key.id}@dutai.site",
            role_id=role.id,
        )

        full_role = RoleRepository(session).get_role_with_permissions(role.id)
        if full_role:
            system_user.role = full_role  # Replace with fully loaded role

        perms = set()
        if system_user.role.role_permissions:
            for rp in system_user.role.role_permissions:
                if rp.permission:
                    perms.add(rp.permission.name)

        system_user.permissions = perms

        set_current_user_id(0)

        return system_user

    # 2. Regular JWT processing
    payload = decode_access_token(token)

    if not payload:
        raise BadRequestException(
            "Invalid or expired token", status.HTTP_401_UNAUTHORIZED
        )

    # Get basic user info from DB (minimal query)
    user = UserRepository(session).get_by_id(payload.sub)

    if not user:
        raise BadRequestException("User not found", status.HTTP_401_UNAUTHORIZED)

    # Claims lúc đăng nhập — dùng cho quyền và các dep đọc _jwt_*
    user.role_name = payload.role or user.role_name
    user.permissions = set(payload.permissions)
    user._jwt_role = user.role_name
    user._jwt_permissions = user.permissions
    if payload.name:
        user._jwt_name = payload.name
    if payload.avatar:
        user._jwt_avatar = payload.avatar

    # Set current user ID in context for audit fields
    set_current_user_id(user.id)

    return user


# Type alias for dependency injection
CurrentUser = Annotated[UserEntity, Depends(get_current_user)]


class PermissionChecker:
    def __init__(self, permission: str | Enum):
        self.permission = (
            permission.value if isinstance(permission, Enum) else permission
        )

    def __call__(self, current_user: CurrentUser) -> UserEntity:
        # Use JWT claims for role/permissions (no DB query needed)
        if not current_user.has_permission(self.permission):
            raise BadRequestException(
                status_code=status.HTTP_403_FORBIDDEN,
                message=f"Missing required permission: {self.permission}",
            )

        return current_user


def hasPermission(permission: str):
    """Dependency factory to check for a specific permission"""
    return Depends(PermissionChecker(permission))


def hasTeamLeaderAccess(target_user_id_param: str = "user_id"):
    async def dependency(request: Request, current_user: CurrentUser):
        jwt_role = getattr(current_user, "_jwt_role", None)
        if jwt_role != RoleType.LEADER.value:
            return  # Admin/other roles bypass

        # Try to get from query params first, then from body
        target_user_id = request.query_params.get(target_user_id_param)
        if not target_user_id:
            data = await request.json()
            target_user_id = data.get(target_user_id_param)

        in_same_team = False

        if not in_same_team:
            raise BadRequestException(
                "Không có quyền vì không chung team",
                status_code=status.HTTP_403_FORBIDDEN,
            )

    return Depends(dependency)


def onlyEditOrDeleteYourself(target_user_id_param: str = "user_id"):
    async def dependency(request: Request, current_user: CurrentUser):
        jwt_role = getattr(current_user, "_jwt_role", None)
        if jwt_role != RoleType.LEADER.value:
            return  # Admin/other roles bypass

        # Try to get from query params first, then from body
        target_user_id = request.query_params.get(target_user_id_param)
        if not target_user_id:
            data = await request.json()
            target_user_id = data.get(target_user_id_param)
        # Check team membership...
        if current_user.id != int(target_user_id):
            raise BadRequestException(
                "Chỉ được edit thông tin bản thân",
                status_code=status.HTTP_403_FORBIDDEN,
            )

    return Depends(dependency)
