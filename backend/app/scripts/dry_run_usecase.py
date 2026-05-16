import asyncio
from datetime import datetime

from app.core.database import get_db
from app.homework.application.use_cases import CheckOverdueHomeworkUseCase
from app.homework.infrastructure.repository import (
    HomeworkSubmissionRepository,
)
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.utils.datetime import get_current_utc7_time


class DryRunEventBus:
    def __init__(self):
        self.events = []

    async def publish(self, event):
        self.events.append(event)
        print(
            f"WOULD PUBLISH VIOLATION: user={event.user_id}, hw={event.homework_id}, reason='{event.reason}'"
        )


async def main():
    async for session in get_db():
        sub_repo = HomeworkSubmissionRepository(session)
        perm_repo = PermissionRequestRepository(session)

        use_case = CheckOverdueHomeworkUseCase(sub_repo, perm_repo)

        import app.homework.application.use_cases

        app.homework.application.use_cases.EventBus.publish = DryRunEventBus().publish
        use_case.event_bus = app.homework.application.use_cases.EventBus

        target_date = datetime.strptime("2026-04-07", "%Y-%m-%d").date()
        print(f"Target date: {target_date}")
        now = get_current_utc7_time().replace(tzinfo=None)
        print(f"Current now evaluated: {now}")

        # Let's inspect the overdue submissions directly
        overdue = sub_repo.get_not_submitted_for_deadline_date(target_date)
        print(f"Found {len(overdue)} overdue submissions for target date.")

        owner_ids = list({sub.owner_id for sub in overdue})
        homework_ids = list({sub.homework_id for sub in overdue if sub.homework_id})

        postpone_requests = perm_repo.get_postpone_requests_for_homeworks(
            homework_ids, owner_ids
        )
        print(
            f"Fetched {len(postpone_requests)} postpone requests matching these HWs and Users."
        )

        req_keys = [(r.created_by, r.homework_id) for r in postpone_requests]
        print(f"Postpone map will have keys: {req_keys}")

        for sub in overdue:
            if sub.owner_id in [13, 15, 12]:
                print(
                    f"Processing target user {sub.owner_id} - hw {sub.homework_id}..."
                )

        # Now do the execute
        await use_case.execute(target_date)
        print("Done dry run.")
        return


if __name__ == "__main__":
    asyncio.run(main())
