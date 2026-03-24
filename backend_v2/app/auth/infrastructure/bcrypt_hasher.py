import bcrypt
from app.auth.domain.interfaces import IPasswordHasher


class BcryptPasswordHasher(IPasswordHasher):
    def hash(self, raw_password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(raw_password.encode("utf-8"), salt).decode("utf-8")

    def verify(self, raw_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(
                raw_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except (ValueError, TypeError):
            return False
