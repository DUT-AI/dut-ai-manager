import os
import sys
import random
import string
from pathlib import Path

# Add the 'backend' directory to sys.path so we can import 'app'
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from sqlalchemy import text
from sqlmodel import Session
from app.core.database import engine
from app.utils.password import get_password_hash


def generate_strong_password() -> str:
    """Generate a random strong password specific format: Xyz@123..."""
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


def reset_password(email: str):
    with Session(engine) as session:
        # 1. Tìm user bằng email
        user_query = text("SELECT id FROM users WHERE email = :email AND is_deleted = False")
        user = session.execute(user_query, {"email": email}).first()

        if not user:
            print(f"Lỗi: Không tìm thấy người dùng (hoặc người dùng đã bị xóa) với email '{email}'.")
            return

        user_id = user[0]

        # 2. Tìm tài khoản liên kết (AccountModel có user_id)
        # Kiểm tra xem account có tồn tại không
        account_check = text("SELECT id FROM accounts WHERE user_id = :user_id AND is_deleted = False")
        account = session.execute(account_check, {"user_id": user_id}).first()
        
        if not account:
            print(f"Lỗi: Không tìm thấy tài khoản cho người dùng '{email}' (ID: {user_id}).")
            return

        # 3. Tạo mật khẩu mới
        new_password = generate_strong_password()
        hashed = get_password_hash(new_password)

        # 4. Hash và cập nhật trong DB
        update_query = text("UPDATE accounts SET hash_password = :hashed, updated_at = NOW() WHERE user_id = :user_id")
        session.execute(update_query, {"hashed": hashed, "user_id": user_id})
        
        # 5. Lưu thay đổi
        session.commit()

        print("--------------------------------------------------")
        print(f"Thay đổi mật khẩu thành công cho: {email}")
        print(f"Mật khẩu mới là: {new_password}")
        print("--------------------------------------------------")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Sử dụng: python scripts/reset_password.py <email>")
        sys.exit(1)

    target_email = sys.argv[1]
    reset_password(target_email)
