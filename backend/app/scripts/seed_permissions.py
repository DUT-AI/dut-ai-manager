from app.core.database import engine
from app.core.permissions import *
from app.models.account import Account
from app.models.permission import Permission
from app.models.role import Role, RoleType
from app.models.user import User, UserStatus
from app.utils.password import hash_password
from loguru import logger
from sqlmodel import Session, select


def seed_roles():
    """
    Seed roles into the database.
    """
    roles_data = [
        {"name": RoleType.ADMIN, "description": "Chủ nhiệm - Toàn quyền hệ thống"},
        {"name": RoleType.LEADER, "description": "Trưởng nhóm - Quản lý thành viên"},
        {"name": RoleType.TEAMMATE, "description": "Thành viên"},
    ]

    with Session(engine) as session:
        for role_data in roles_data:
            # Check if role already exists
            statement = select(Role).where(Role.name == role_data["name"])
            existing_role = session.exec(statement).first()

            if existing_role:
                logger.info(
                    f"Role '{role_data['name'].value}' already exists, skipping..."
                )
                continue

            # Create new role
            new_role = Role(
                name=role_data["name"],
                description=role_data["description"],
            )
            session.add(new_role)
            logger.success(f"Added role: {role_data['name'].value}")

        session.commit()
        logger.info("Role seeding completed.")


def seed_admin_user():
    """
    Seed admin user into the database.
    """
    admin_data = {
        "name": "Huỳnh Phước Nguyên",
        "email": "huynhphuocnguyen.dev@gmail.com",
        "phone_number": "0931960822",
    }

    with Session(engine) as session:
        # Check if admin already exists
        statement = select(User).where(User.email == admin_data["email"])
        existing_user = session.exec(statement).first()

        if existing_user:
            logger.info(
                f"Admin user '{admin_data['email']}' already exists, skipping..."
            )
            return

        # Get admin role
        role_statement = select(Role).where(Role.name == RoleType.ADMIN)
        admin_role = session.exec(role_statement).first()

        if not admin_role:
            logger.error("Admin role not found. Please run seed_roles first.")
            return

        # Create account with phone_number as password
        account = Account(hash_password=hash_password(admin_data["phone_number"]))
        session.add(account)
        session.flush()  # Get the account ID

        # Create user
        user = User(
            name=admin_data["name"],
            email=admin_data["email"],
            phone_number=admin_data["phone_number"],
            status=UserStatus.ACTIVE,
            role_id=admin_role.id,
            account_id=account.id,
        )
        session.add(user)
        session.commit()
        logger.success(
            f"Added admin user: {admin_data['name']} ({admin_data['email']})"
        )


def seed_permissions():
    """
    Seed permissions into the database based on the enums defined in app/core/permissions.py.
    """
    permission_enums = [
        RolePermission,
        UserPermission,
        BonusPointPermission,
        ViolationPermission,
        TeamPermission,
        TeamMemberPermission,
        HomeworkPermission,
        HomeworkSubmissionPermission,
        PermissionPermission,
        PermissionRequestPermission,
        MeetingPermission,
    ]

    with Session(engine) as session:
        for enum_class in permission_enums:
            for enum_member in enum_class:
                perm_name = enum_member.value

                # Split permission name into resource and action (e.g., "user:create" -> "user", "create")
                try:
                    resource, action = perm_name.split(":")
                except ValueError:
                    logger.warning(f"Invalid permission name format: {perm_name}")
                    continue

                # Check if permission already exists
                statement = select(Permission).where(Permission.name == perm_name)
                existing_perm = session.exec(statement).first()

                if existing_perm:
                    logger.info(f"Permission '{perm_name}' already exists, skipping...")
                    continue

                # Create new permission
                new_perm = Permission(
                    name=perm_name,
                    resource=resource,
                    action=action,
                    description=f"Allow {action} on {resource}",
                )
                session.add(new_perm)
                logger.success(f"Added permission: {perm_name}")

        session.commit()
        logger.info("Permission seeding completed.")


if __name__ == "__main__":
    seed_roles()
    seed_permissions()
    seed_admin_user()
