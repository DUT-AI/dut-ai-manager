"""
Base Task Scanner interface and Candidate Task Item model.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from app.reminder.domain.entity import ReminderStage, TaskType


@dataclass
class ScannedCandidateTask:
    task_type: TaskType
    task_id: int
    task_title: str
    user_id: int
    deadline: datetime
    action_url: str
    stages: list[ReminderStage]


class BaseTaskScanner(ABC):
    @abstractmethod
    def scan_pending_tasks(self, now: datetime) -> list[ScannedCandidateTask]:
        """Quét và trả về danh sách các ứng viên nhiệm vụ sắp đến hạn chưa hoàn thành."""
        pass


def calculate_matching_stages(deadline: datetime, now: datetime) -> list[ReminderStage]:
    """Hàm ủy quyền gọi trực tiếp logic của Domain Entity ReminderStage."""
    return ReminderStage.calculate_matching_stages(deadline=deadline, now=now)
