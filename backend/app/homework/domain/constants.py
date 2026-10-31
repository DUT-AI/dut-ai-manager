"""
Domain Constants for Homework Domain.
"""

from app.violation.domain.constants import DEFAULT_VIOLATION_CHECK_DELAY_DAYS

# Delay in days before scheduled job checks for overdue homework submissions.
HOMEWORK_VIOLATION_CHECK_DELAY_DAYS: int = DEFAULT_VIOLATION_CHECK_DELAY_DAYS
