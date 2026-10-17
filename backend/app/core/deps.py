from enum import Enum
from typing import Annotated, cast

from fastapi import Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.context import set_current_user_id
from app.core.database import get_session
from app.core.principal import AuthPrincipal, PrincipalType
from app.rbac.domain.entity import RoleType
from app.rbac.infrastructure.repository import RoleApiKeyRepository, RoleRepository
from app.shared.application.response import BadRequestException
from app.utils.password import decode_access_token, verify_password

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


def get_current_principal(
    token: Annotated[str, Depends(get_token_from_cookie_or_header)],
    session: Annotated[Session, Depends(get_session)],
) -> AuthPrincipal:
    """
    Get current authenticated principal from token.
    Supports:
    1. API Key (Role-based system access)
    2. JWT Access Token (User login)
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
            raise BadRequestException("Invalid API Key", status_code=status.HTTP_401_UNAUTHORIZED)

        role = matched_key.role
        if not role:
            raise BadRequestException("Role not found", status_code=status.HTTP_401_UNAUTHORIZED)

        full_role = RoleRepository(session).get_role_with_permissions(
            cast(int, role.id)
        )
        perms: set[str] = set()
        role_names: list[str] = []
        if full_role:
            if full_role.name:
                role_names.append(full_role.name)
            if full_role.role_permissions:
                for rp in full_role.role_permissions:
                    if rp.permission:
                        perms.add(rp.permission.name)

        # Do not assign fake user ID to avoid DB foreign key collisions
        set_current_user_id(None)

        return AuthPrincipal(
            actor_id=matched_key.id,
            actor_type=PrincipalType.API_KEY,
            name=f"System: {matched_key.name}",
            role_names=role_names,
            permissions=perms,
        )

    # 2. Regular JWT processing (Fast-path: load roles & permissions from JWT claims)
    payload = decode_access_token(token)

    if not payload:
        raise BadRequestException(
            "Invalid or expired token", status_code=status.HTTP_401_UNAUTHORIZED
        )

    # Set current user ID in context for audit fields
    set_current_user_id(payload.sub)

    return AuthPrincipal(
        actor_id=payload.sub,
        actor_type=PrincipalType.USER,
        name=payload.name,
        email=payload.email,
        role_names=payload.roles,
        permissions=set(payload.permissions),
    )


# Type alias for dependency injection
get_current_user = get_current_principal
CurrentUser = Annotated[AuthPrincipal, Depends(get_current_principal)]


class PermissionChecker:
    def __init__(self, permission: str | Enum):
        self.permission = (
            permission.value if isinstance(permission, Enum) else permission
        )

    def __call__(self, current_user: CurrentUser) -> AuthPrincipal:
        if not current_user.has_permission(self.permission):
            raise BadRequestException(
                status_code=status.HTTP_403_FORBIDDEN,
                message=f"Missing required permission: {self.permission}",
            )

        return current_user


def hasPermission(permission: str | Enum):
    """Dependency factory to check for a specific permission"""
    return Depends(PermissionChecker(permission))


def hasTeamLeaderAccess(target_user_id_param: str = "user_id"):
    async def dependency(request: Request, current_user: CurrentUser):
        roles_lower = [r.lower() for r in current_user.role_names]
        if RoleType.ADMIN.value.lower() in roles_lower:
            return  # Admin bypasses team check

        if RoleType.LEADER.value.lower() not in roles_lower:
            raise BadRequestException(
                "Không có quyền truy cập",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        # Try to get from query params first, then from body
        target_user_id = request.query_params.get(target_user_id_param)
        if not target_user_id:
            try:
                data = await request.json()
                target_user_id = data.get(target_user_id_param)
            except Exception:
                target_user_id = None

        in_same_team = False

        if not in_same_team:
            raise BadRequestException(
                "Không có quyền vì không chung team",
                status_code=status.HTTP_403_FORBIDDEN,
            )

    return Depends(dependency)


def onlyEditOrDeleteYourself(target_user_id_param: str = "user_id"):
    async def dependency(request: Request, current_user: CurrentUser):
        roles_lower = [r.lower() for r in current_user.role_names]
        if RoleType.ADMIN.value.lower() in roles_lower:
            return  # Admin bypasses self check

        # Try to get from query params first, then from body
        target_user_id = request.query_params.get(target_user_id_param)
        if not target_user_id:
            try:
                data = await request.json()
                target_user_id = data.get(target_user_id_param)
            except Exception:
                target_user_id = None

        if (
            not current_user.is_user
            or current_user.id is None
            or target_user_id is None
            or current_user.id != int(target_user_id)
        ):
            raise BadRequestException(
                "Chỉ được edit thông tin bản thân",
                status_code=status.HTTP_403_FORBIDDEN,
            )

    return Depends(dependency)
