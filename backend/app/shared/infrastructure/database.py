"""
Database configuration and session management.

Session lifecycle:
    - Each request gets ONE session
    - Repository methods use flush() (not commit) for intermediate operations
    - Session auto-commits on success, auto-rollbacks on exception
    - This ensures ALL operations in a request = 1 atomic transaction
"""

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, configure_mappers

from app.core.config import settings
from app.shared.infrastructure.base_model import Base

# Create engine
engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    echo=settings.ENVIRONMENT == "local",
)


def import_all_models():
    """Import all ORM models to register with Base before configuring mappers."""
    import app.auth.infrastructure.model
    import app.billing.infrastructure.model
    import app.bonus_point.infrastructure.model
    import app.expense.infrastructure.model
    import app.homework.infrastructure.model
    import app.meeting.infrastructure.model
    import app.permission_request.infrastructure.model
    import app.rbac.infrastructure.model
    import app.team.infrastructure.model
    import app.user.infrastructure.model
    import app.violation.infrastructure.model

import_all_models()
configure_mappers()


def create_db_and_tables():
    """Create all database tables."""

    configure_mappers()
    Base.metadata.create_all(engine)


def get_session():
    """
    Get database session with auto-commit/rollback.

    On success: commits the transaction
    On exception: rolls back and re-raises
    """
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            logger.error("Session rollback due to exception")
            raise
