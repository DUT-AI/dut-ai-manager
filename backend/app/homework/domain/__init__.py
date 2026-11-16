"""Homework domain package."""

from app.homework.domain.constants import HOMEWORK_VIOLATION_CHECK_DELAY_DAYS
from app.homework.domain.entity import (
    Homework,
    HomeworkAssignee,
    HomeworkSubmission,
    SubmissionType,
)
from app.homework.domain.ports import (
    HomeworkAssigneeRepositoryPort,
    HomeworkRepositoryPort,
    HomeworkSubmissionRepositoryPort,
)
from app.homework.domain.value_objects import (
    AssigneeUserInfo,
    DueHomeworkAssignment,
    HomeworkOverdueDetected,
)

__all__ = [
    "AssigneeUserInfo",
    "HOMEWORK_VIOLATION_CHECK_DELAY_DAYS",
    "DueHomeworkAssignment",
    "Homework",
    "HomeworkAssignee",
    "HomeworkAssigneeRepositoryPort",
    "HomeworkOverdueDetected",
    "HomeworkRepositoryPort",
    "HomeworkSubmission",
    "HomeworkSubmissionRepositoryPort",
    "SubmissionType",
]
