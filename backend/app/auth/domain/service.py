from typing import Tuple
import random
import string

from app.auth.domain.entity import Account
from app.utils.password import hash_password


class AuthService:
    def create_account(self, user_id: int) -> Tuple[str, Account]:
        password = self._generate_strong_password()
        account = Account(hash_password=hash_password(password), user_id=user_id)
        return password, account

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
