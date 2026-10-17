"""Creates a new DB account and strong random password."""

import random
import string

from app.auth.domain.entity import Account
from app.auth.infrastructure.repository import AccountRepository
from app.user.infrastructure.repository import UserRepository
from app.utils.password import hash_password


class CreateAccountUseCase:
    """Creates a new DB account and strong random password. Typically used internally by User generation."""

    def __init__(self, account_repo: AccountRepository, user_repo: UserRepository | None = None):
        self.account_repo = account_repo
        self.user_repo = user_repo

    def execute(self, user_id: int | None = None) -> tuple[Account, str]:
        password = self._generate_strong_password()
        account = Account(hash_password=hash_password(password), user_id=user_id)
        saved = self.account_repo.add(account)
        return saved, password

    def _generate_strong_password(self) -> str:
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        symbols = "@#$!%*?&"

        password_chars = [
            random.choice(uppercase),
            random.choice(lowercase),
            random.choice(digits),
            random.choice(symbols),
        ]
        all_chars = lowercase + uppercase + digits + symbols
        length = random.randint(10, 12)
        for _ in range(length - 4):
            password_chars.append(random.choice(all_chars))

        random.shuffle(password_chars)
        return "".join(password_chars)
