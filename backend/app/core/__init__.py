"""Core package re-exports for convenience."""

from app.core.deps import (
    CurrentUser,
    CurrentUserEntity,
    PermissionChecker,
    get_current_principal,
    get_current_user,
    get_current_user_entity,
    hasPermission,
)
from app.core.principal import AuthPrincipal, PrincipalType

__all__ = [
    "AuthPrincipal",
    "PrincipalType",
    "CurrentUser",
    "CurrentUserEntity",
    "PermissionChecker",
    "hasPermission",
    "get_current_principal",
    "get_current_user",
    "get_current_user_entity",
]
