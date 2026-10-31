"""
Domain Constants for Violation Domain.
"""

# Default delay in days for scheduled background violation checks.
# Scheduled jobs check events from (today - DEFAULT_VIOLATION_CHECK_DELAY_DAYS).
DEFAULT_VIOLATION_CHECK_DELAY_DAYS: int = 2
