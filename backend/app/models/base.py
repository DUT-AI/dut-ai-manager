"""
Backward compatibility — re-exports TimestampMixin from shared infrastructure.

New modules should import from: app.shared.infrastructure.base_model
"""

from app.shared.infrastructure.base_model import TimestampMixin

__all__ = ["TimestampMixin"]
