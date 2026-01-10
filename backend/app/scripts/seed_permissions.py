from sqlmodel import Session, select
from app.core.database import engine
from app.models.permission import Permission
from app.core.permissions import *
from loguru import logger


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
    seed_permissions()
