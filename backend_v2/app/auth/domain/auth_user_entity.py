from typing import Optional

from app.shared.base_entity import BaseEntity
from app.user.domain.value_objects import \
  UserStatus  # Reuse Enum, or redefine it here? Let's reuse Enum.


class AuthUser(BaseEntity):
    """
    Tách biệt Domain Auth hoàn toàn với User.
    Entity này chỉ định nghĩa các trường liên lạc được cấp cho nghiệp vụ đăng nhập, đổi mật khẩu.
    """

    email: str
    hashed_password: str
    status: UserStatus = UserStatus.ACTIVE

    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE
