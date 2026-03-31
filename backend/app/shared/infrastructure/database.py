"""
Database configuration and session management.

Session lifecycle:
    - Each request gets ONE session
    - Repository methods use flush() (not commit) for intermediate operations
    - Session auto-commits on success, auto-rollbacks on exception
    - This ensures ALL operations in a request = 1 atomic transaction
"""

from app.core.config import settings
from loguru import logger
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.orm import configure_mappers

# Create engine
engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    echo=settings.ENVIRONMENT == "local",
)


def create_db_and_tables():
    """Create all database tables."""

    configure_mappers()
    SQLModel.metadata.create_all(engine)


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
