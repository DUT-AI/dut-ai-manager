"""
Domain Constants for Meeting Domain.
"""

from app.violation.domain.constants import DEFAULT_VIOLATION_CHECK_DELAY_DAYS

# Delay in days before scheduled job checks for meeting attendance
MEETING_ATTENDANCE_CHECK_DELAY_DAYS: int = DEFAULT_VIOLATION_CHECK_DELAY_DAYS

# Deadline in hours after meeting end_time before unsubmitted evaluations trigger violations.
# Originally 24 hours, delayed by 2 days (48 hours) -> 72 hours.
MEETING_EVALUATION_DEADLINE_HOURS: int = 72

# Scan window in days to look back for ended meetings when checking evaluations
MEETING_EVALUATION_SCAN_WINDOW_DAYS: int = 9
