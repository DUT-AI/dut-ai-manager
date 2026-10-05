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
from sqlalchemy.orm import Session

from app.core.config import settings

# Create engine
engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    echo=settings.ENVIRONMENT == "local",
)



from app.shared.application.response import BadRequestException

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
        except BadRequestException:
            session.rollback()
            logger.info("Session rollback due to BadRequest validation failure")
            raise
        except Exception:
            session.rollback()
            logger.error("Session rollback due to unexpected system exception", exc_info=True)
            raise
