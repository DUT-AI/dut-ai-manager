"""
Scan And Send Reminders Use Case (Orchestrator).
Orchestrates candidate task scanners, applies deduplication/cooldown filters,
and delegates dispatching to ReminderDispatcher using unified NotificationRepository.
"""

from datetime import UTC, datetime

from app.reminder.application.dtos import (
    ReminderScanDetailDto,
    TriggerReminderScanResponseDto,
)
from app.reminder.application.reminder_dispatcher import ReminderDispatcher
from app.reminder.application.scanners.base_scanner import BaseTaskScanner
from app.reminder.domain.entity import (
    Notification,
    ReminderStatus,
)
from app.reminder.infrastructure.repository import NotificationRepository


class ScanAndSendRemindersUseCase:
    def __init__(
        self,
        scanners: list[BaseTaskScanner],
        dispatcher: ReminderDispatcher,
        notification_repo: NotificationRepository,
    ):
        self.scanners = scanners
        self.dispatcher = dispatcher
        self.notification_repo = notification_repo

    async def execute(
        self,
        dry_run: bool = False,
        now: datetime | None = None,
    ) -> TriggerReminderScanResponseDto:
        if now is None:
            now = datetime.now(UTC)

        total_scanned = 0
        total_sent = 0
        total_skipped = 0
        total_failed = 0
        details: list[ReminderScanDetailDto] = []

        # Quét lần lượt qua các Task Scanner độc lập
        for scanner in self.scanners:
            candidate_tasks = scanner.scan_pending_tasks(now=now)
            total_scanned += len(candidate_tasks)

            for task in candidate_tasks:
                for stage in task.stages:
                    # 1. Kiểm tra deduplication: mốc này đã gửi cho task của user chưa
                    if self.notification_repo.has_reminder_been_sent(
                        task_type=task.task_type,
                        task_id=task.task_id,
                        user_id=task.user_id,
                        stage=stage,
                    ):
                        total_skipped += 1
                        continue

                    # 2. Cooldown check: Kiểm tra thời gian giãn cách theo Entity domain logic
                    last_sent = self.notification_repo.get_last_reminder_time(
                        task_type=task.task_type,
                        task_id=task.task_id,
                        user_id=task.user_id,
                    )
                    if Notification.is_within_cooldown(
                        last_sent_at=last_sent,
                        now=now,
                        stage=stage,
                    ):
                        total_skipped += 1
                        continue

                    if dry_run:
                        total_sent += 1
                        details.append(
                            ReminderScanDetailDto(
                                task_type=task.task_type,
                                task_id=task.task_id,
                                user_id=task.user_id,
                                stage=stage,
                                status=ReminderStatus.SENT,
                            )
                        )
                        continue

                    # 3. Phát thông báo qua Dispatcher
                    status = await self.dispatcher.dispatch(
                        task_type=task.task_type,
                        task_id=task.task_id,
                        task_title=task.task_title,
                        user_id=task.user_id,
                        deadline=task.deadline,
                        stage=stage,
                        action_url=task.action_url,
                        now=now,
                    )

                    if status == ReminderStatus.SENT:
                        total_sent += 1
                    else:
                        total_failed += 1

                    details.append(
                        ReminderScanDetailDto(
                            task_type=task.task_type,
                            task_id=task.task_id,
                            user_id=task.user_id,
                            stage=stage,
                            status=status,
                        )
                    )

        return TriggerReminderScanResponseDto(
            scanned_at=now,
            total_tasks_scanned=total_scanned,
            total_reminders_sent=total_sent,
            total_skipped_already_sent=total_skipped,
            total_failed=total_failed,
            details=details,
        )
