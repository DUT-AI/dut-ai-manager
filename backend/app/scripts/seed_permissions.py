from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

import app.meeting.infrastructure.model  # noqa: F401
from app.auth.infrastructure.model import AccountModel
from app.core.database import engine
from app.core.permissions import (
    AccountPermission,
    BillingPermission,
    BonusPointPermission,
    DutyPermission,
    ExpensePermission,
    HomeworkPermission,
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
            existing_role = session.scalars(statement).first()

            if existing_role:
                logger.info(f"Role '{role_data['name']}' already exists, skipping...")
                continue

            # Create new role
            new_role = RoleModel(
                name=role_data["name"],
                description=role_data["description"],
            )
            session.add(new_role)
            logger.success(f"Added role: {role_data['name']}")

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
        existing_user = session.scalars(statement).first()

        if existing_user:
            logger.info(
                f"Admin user '{admin_data['email']}' already exists, skipping..."
            )
            return

        # Get admin role
        role_statement = select(RoleModel).where(RoleModel.name == RoleType.ADMIN)
        admin_role = session.scalars(role_statement).first()

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
        PermissionPermission,
        PermissionRequestPermission,
        MeetingPermission,
        AccountPermission,
        BillingPermission,
        ExpensePermission,
        DutyPermission,
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
                existing_perm = session.scalars(statement).first()

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
        admin_role = session.scalars(
            select(RoleModel).where(RoleModel.name == RoleType.ADMIN)
        ).first()

        if not admin_role:
            logger.error("Admin role not found. Please run seed_roles first.")
            return

        # Get all permissions
        all_permissions = session.scalars(select(PermissionModel)).all()

        # Get existing role permissions to avoid duplicates
        existing_perm_ids = session.scalars(
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


def sync_member_duty_permissions():
    """
    Ensure:
    - Admin and HR have all duty permissions (create, read, update, delete, submit).
    - Teammate ONLY has duty:read.
    - Leader has NO duty permissions.
    """
    with Session(engine) as session:
        all_duty_perms = session.scalars(
            select(PermissionModel).where(PermissionModel.resource == "duty")
        ).all()
        duty_perm_map = {p.action: p.id for p in all_duty_perms}
        all_duty_perm_ids = {p.id for p in all_duty_perms}
        duty_read_id = duty_perm_map.get("read")

        roles = session.scalars(select(RoleModel)).all()
        for role in roles:
            role_name_upper = role.name.upper()

            # 1. Admin and HR: Grant ALL duty permissions
            if role_name_upper in ["ADMIN", "HR"]:
                existing_perm_ids = set(
                    session.scalars(
                        select(RolePermissionModel.permission_id).where(
                            RolePermissionModel.role_id == role.id
                        )
                    ).all()
                )
                for perm in all_duty_perms:
                    if perm.id not in existing_perm_ids:
                        session.add(
                            RolePermissionModel(role_id=role.id, permission_id=perm.id)
                        )
                        logger.info(f"Granted {perm.name} to {role.name} role")
                continue

            # 2. Leader: Remove any duty permissions (No leader in duty module)
            if role_name_upper == "LEADER":
                duty_role_perms = session.scalars(
                    select(RolePermissionModel).where(
                        RolePermissionModel.role_id == role.id,
                        RolePermissionModel.permission_id.in_(all_duty_perm_ids),
                    )
                ).all()
                for rp in duty_role_perms:
                    session.delete(rp)
                    logger.info(
                        f"Revoked duty permission id {rp.permission_id} from LEADER role"
                    )
                continue

            # 3. Teammate: ONLY read permission
            if role_name_upper == "TEAMMATE":
                # Revoke any duty permissions that are NOT duty:read
                non_read_ids = all_duty_perm_ids - (
                    {duty_read_id} if duty_read_id else set()
                )
                non_read_duty_perms = session.scalars(
                    select(RolePermissionModel).where(
                        RolePermissionModel.role_id == role.id,
                        RolePermissionModel.permission_id.in_(non_read_ids),
                    )
                ).all()
                for rp in non_read_duty_perms:
                    session.delete(rp)
                    logger.info(
                        f"Revoked non-read duty permission id {rp.permission_id} from TEAMMATE role"
                    )

                # Grant duty:read if not present
                existing_perm_ids = set(
                    session.scalars(
                        select(RolePermissionModel.permission_id).where(
                            RolePermissionModel.role_id == role.id
                        )
                    ).all()
                )
                if duty_read_id and duty_read_id not in existing_perm_ids:
                    session.add(
                        RolePermissionModel(role_id=role.id, permission_id=duty_read_id)
                    )
                    logger.info("Granted duty:read to TEAMMATE role")
                continue

            # 4. Other roles: Remove any duty permissions
            other_duty_perms = session.scalars(
                select(RolePermissionModel).where(
                    RolePermissionModel.role_id == role.id,
                    RolePermissionModel.permission_id.in_(all_duty_perm_ids),
                )
            ).all()
            for rp in other_duty_perms:
                session.delete(rp)

        session.commit()
        logger.info(
            "Duty permissions sync completed: Leader has none, Teammate is read-only."
        )


if __name__ == "__main__":
    seed_roles()
    seed_permissions()
    seed_admin_user()
    sync_admin_permissions()
    sync_member_duty_permissions()
