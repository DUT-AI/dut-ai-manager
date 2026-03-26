import os
import sys

# Add the current directory to sys.path so we can import 'app'
sys.path.append(os.getcwd())

from app.core.container import AppContainer
from app.core.database import engine
from app.core.repository_factory import RepositoryFactory
from app.core.service_factory import ServiceFactory
from app.utils.password import hash_password
from sqlmodel import Session


def reset_password(email: str):
    container = AppContainer()
    with Session(engine) as session:
        repo_factory = RepositoryFactory(session)
        service_factory = ServiceFactory(
            repo_factory,
            minio_service=container.minio_service,
            discord_service=container.discord_service,
            email_service=container.email_service,
        )

        # 1. Tìm user bằng email
        user = repo_factory.user.get_by_email(email)
        if not user:
            print(f"Lỗi: Không tìm thấy người dùng với email '{email}'.")
            return

        # 2. Lấy tài khoản tương ứng
        account = repo_factory.account.get_by_id(user.account_id)
        if not account:
            print(f"Lỗi: Không tìm thấy thông tin tài khoản cho người dùng '{email}'.")
            return

        # 3. Tạo mật khẩu mới ngẫu nhiên (sử dụng hàm có sẵn trong AuthService)
        new_password = service_factory.auth.generate_strong_password()

        # 4. Hash mật khẩu mới và cập nhật
        account.hash_password = hash_password(new_password)
        repo_factory.account.update(account)

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
