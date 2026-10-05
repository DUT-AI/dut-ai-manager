"""
Backward compatibility — re-exports from shared infrastructure.

New modules should import from: app.shared.infrastructure.database
"""

from app.shared.infrastructure.database import engine, get_session

__all__ = ["engine", "get_session"]
