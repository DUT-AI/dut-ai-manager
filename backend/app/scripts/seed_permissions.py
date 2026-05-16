from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.infrastructure.model import AccountModel
from app.core.database import engine
from app.core.permissions import (
    AccountPermission,
    BillingPermission,
    BonusPointPermission,
    HomeworkPermission,
    HomeworkSubmissionPermission,
    MeetingPermission,
    PermissionPermission,
    PermissionRequestPermission,
    RolePermission,
    TeamMemberPermission,
    TeamPermission,
    UserPermission,
    ViolationPermission,
)
from app.rbac.domain.entity import RoleType
from app.rbac.infrastructure.model import (
    PermissionModel,
    RoleModel,
    RolePermissionModel,
)
from app.user.domain.entity import UserStatus
from app.user.infrastructure.model import UserModel
from app.utils.password import hash_password

# Import other models to register them in SQLModel registry for relationships


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
            statement = select(RoleModel).where(RoleModel.name == role_data["name"])
            existing_role = session.exec(statement).first()

            if existing_role:
                logger.info(
                    f"Role '{role_data['name'].value}' already exists, skipping..."
                )
                continue

            # Create new role
            new_role = RoleModel(
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
        statement = select(UserModel).where(UserModel.email == admin_data["email"])
        existing_user = session.exec(statement).first()

        if existing_user:
            logger.info(
                f"Admin user '{admin_data['email']}' already exists, skipping..."
            )
            return

        # Get admin role
        role_statement = select(RoleModel).where(RoleModel.name == RoleType.ADMIN)
        admin_role = session.exec(role_statement).first()

        if not admin_role:
            logger.error("Admin role not found. Please run seed_roles first.")
            return

        # Create user first (in new model structure, Account has user_id)
        user = UserModel(
            name=admin_data["name"],
            email=admin_data["email"],
            phone_number=admin_data["phone_number"],
            status=UserStatus.ACTIVE,
            role_id=admin_role.id,
        )
        session.add(user)
        session.flush()  # Get user.id

        # Create account with phone_number as password linked to user
        account = AccountModel(
            hash_password=hash_password(admin_data["phone_number"]), user_id=user.id
        )
        session.add(account)

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
        AccountPermission,
        BillingPermission,
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
                statement = select(PermissionModel).where(
                    PermissionModel.name == perm_name
                )
                existing_perm = session.exec(statement).first()

                if existing_perm:
                    logger.info(f"Permission '{perm_name}' already exists, skipping...")
                    continue

                # Create new permission
                new_perm = PermissionModel(
                    name=perm_name,
                    resource=resource,
                    action=action,
                    description=f"Allow {action} on {resource}",
                )
                session.add(new_perm)
                logger.success(f"Added permission: {perm_name}")

        session.commit()
        logger.info("Permission seeding completed.")


def sync_admin_permissions():
    """
    Ensure the Admin role has ALL permissions defined in the database.
    """
    with Session(engine) as session:
        # Get admin role
        admin_role = session.exec(
            select(RoleModel).where(RoleModel.name == RoleType.ADMIN)
        ).first()

        if not admin_role:
            logger.error("Admin role not found. Please run seed_roles first.")
            return

        # Get all permissions
        all_permissions = session.exec(select(PermissionModel)).all()

        # Get existing role permissions to avoid duplicates
        existing_perm_ids = session.exec(
            select(RolePermissionModel.permission_id).where(
                RolePermissionModel.role_id == admin_role.id
            )
        ).all()

        added_count = 0
        for perm in all_permissions:
            if perm.id not in existing_perm_ids:
                role_perm = RolePermissionModel(
                    role_id=admin_role.id, permission_id=perm.id
                )
                session.add(role_perm)
                added_count += 1

        session.commit()
        if added_count > 0:
            logger.success(f"Synced {added_count} new permissions to Admin role.")
        else:
            logger.info("Admin role already has all permissions.")


if __name__ == "__main__":
    seed_roles()
    seed_permissions()
    seed_admin_user()
    sync_admin_permissions()
