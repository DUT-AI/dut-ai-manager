"""
Backward compatibility — re-exports from shared infrastructure.

New modules should import from: app.shared.infrastructure.database
"""

from app.shared.infrastructure.database import create_db_and_tables, engine, get_session

__all__ = ["engine", "create_db_and_tables", "get_session"]
