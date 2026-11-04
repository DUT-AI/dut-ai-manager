import os
import socket
import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class LeaderRole(StrEnum):
    """Role of the worker in the distributed scheduler coordination."""

    LEADER = "LEADER"
    STANDBY = "STANDBY"


@dataclass(frozen=True)
class WorkerIdentity:
    """Unique identity snapshot for a worker process."""

    hostname: str
    pid: int
    instance_id: str

    @property
    def worker_id(self) -> str:
        return f"{self.hostname}:{self.pid}:{self.instance_id}"

    @classmethod
    def create(cls) -> "WorkerIdentity":
        return cls(
            hostname=socket.gethostname(),
            pid=os.getpid(),
            instance_id=uuid.uuid4().hex[:8],
        )


@dataclass
class SchedulerCoordinatorState:
    """In-memory coordinator state for the worker instance."""

    worker_id: str
    role: LeaderRole = LeaderRole.STANDBY
    is_running: bool = False
    heartbeat_task: Any = field(default=None)
    standby_task: Any = field(default=None)
    scheduler_instance: Any = field(default=None)
