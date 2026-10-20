"""
DTOs for Reminder & Notification application use cases.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.reminder.domain.entity import (
    NotificationCategory,
    NotificationLevel,
    ReminderStage,
    ReminderStatus,
    TaskType,
)


class NotificationDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    content: str
    category: NotificationCategory
    level: NotificationLevel
    action_url: str | None = None
    is_read: bool = False
    read_at: datetime | None = None
    created_at: datetime


class UnreadCountDto(BaseModel):
    unread_count: int


class ReminderScanDetailDto(BaseModel):
    task_type: TaskType
    task_id: int
    user_id: int
    stage: ReminderStage
    status: ReminderStatus


class TriggerReminderScanResponseDto(BaseModel):
    scanned_at: datetime
    total_tasks_scanned: int
    total_reminders_sent: int
    total_skipped_already_sent: int
    total_failed: int
    details: list[ReminderScanDetailDto] = []


class PendingTaskDto(BaseModel):
    task_type: TaskType
    task_id: int
    title: str
    deadline: datetime
    hours_remaining: float
    urgency_level: str
    action_url: str
