"""
Homework Checker Use Cases — application layer.

Handles daily background job (23:59) checking for overdue homework submissions and creating system violations.
"""

from datetime import date
from typing import cast

from loguru import logger

from app.homework.application.helpers import QuizSubmissionHelper
from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.domain.value_objects import HomeworkOverdueDetected
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.homework.infrastructure.repository import HomeworkRepository
from app.permission_request.domain.value_objects import RequestCategory
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.shared.domain.event_bus import DomainEvent, EventBus
from app.team.infrastructure.repository import TeamRepository
from app.user.infrastructure.repository import UserRepository
from app.utils.datetime import get_current_utc7_time


class CheckOverdueHomeworkUseCase:
    """Kiểm tra bài tập quá hạn và tạo vi phạm tự động dựa trên kết quả từ Quiz API."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        permission_repo: PermissionRequestRepository,
        quiz_api: QuizApiClient,
        user_repo: UserRepository,
        team_repo: TeamRepository | None = None,
        event_bus: type[EventBus] = EventBus,
    ):
        self.homework_repo = homework_repo
        self.permission_repo = permission_repo
        self.quiz_api = quiz_api
        self.user_repo = user_repo
        self.team_repo = team_repo
        self.event_bus = event_bus

    def _get_effective_assigned_user_ids(self, homework: HomeworkEntity) -> set[int]:
        assigned_uids: set[int] = set()
        user_ids = getattr(homework, "assignee_ids", None) or getattr(homework, "assigned_user_ids", None)
        if user_ids:
            assigned_uids.update(user_ids)

        team_ids = getattr(homework, "team_ids", None) or getattr(homework, "assigned_team_ids", None)
        if team_ids and self.team_repo:
            team_user_ids = self.team_repo.get_user_ids_by_teams(team_ids)
            assigned_uids.update(team_user_ids)

        if not assigned_uids and homework.id and hasattr(self.homework_repo, "get_assigned_user_ids"):
            repo_uids = self.homework_repo.get_assigned_user_ids(homework.id)
            if repo_uids:
                assigned_uids.update(repo_uids)

        if not assigned_uids and hasattr(self, "user_repo") and self.user_repo:
            active_users = self.user_repo.get_active_users()
            assigned_uids.update({u.id for u in active_users if u.id is not None})

        return assigned_uids

    async def execute(self, target_date: date | None = None) -> int:
        """
        Quét tất cả các bài tập có deadline là target_date (mặc định là hôm nay):
        1. Lấy danh sách thành viên được phân công.
        2. Kiểm tra xem họ có hoàn thành Coding và Game (nếu có) trên Quiz API không.
        3. Nếu CHƯA hoàn thành:
           - Kiểm tra xem có đơn xin tạm hoãn (POSTPONE) chưa hết hạn hay không.
           - Nếu KHÔNG có đơn hợp lệ -> Phát sự kiện HomeworkOverdueDetected để hệ thống tự động tạo Vi phạm.
        """
        if target_date is None:
            now = get_current_utc7_time()
            target_date = now.date()

        due_homeworks = self.homework_repo.get_by_deadline_date(target_date)
        if not due_homeworks:
            logger.info(f"Không có bài tập nào có deadline vào ngày {target_date}")
            return 0

        created_violations_count = 0

        for homework in due_homeworks:
            if not homework.id:
                continue

            slug = QuizSubmissionHelper.extract_slug_from_entity(homework)
            if not slug:
                logger.warning(
                    f"Bài tập id={homework.id} '{homework.title}' không có slug/link hợp lệ để gọi Quiz API. Bỏ qua."
                )
                continue

            coding_completed_uids = await QuizSubmissionHelper.get_coding_completed_user_ids(self.quiz_api, slug)
            game_completed_uids = await QuizSubmissionHelper.get_game_completed_user_ids(self.quiz_api, slug)

            assigned_uids = self._get_effective_assigned_user_ids(homework)
            if not assigned_uids:
                continue

            postpone_requests = self.permission_repo.get_postpone_requests_for_homeworks(
                homework_ids=[homework.id], user_ids=list(assigned_uids)
            )
            postpone_map = {(r.created_by, r.homework_id): r for r in postpone_requests}

            now_naive = get_current_utc7_time().replace(tzinfo=None)

            for user_id in assigned_uids:
                is_coding_done = (
                    coding_completed_uids is not None and user_id in coding_completed_uids
                )
                is_game_done = (
                    game_completed_uids is not None and user_id in game_completed_uids
                )

                uncompleted_types = []
                if coding_completed_uids is not None and not is_coding_done:
                    uncompleted_types.append("code")
                if game_completed_uids is not None and not is_game_done:
                    uncompleted_types.append("game")

                if not uncompleted_types:
                    continue

                req = postpone_map.get((user_id, homework.id))
                has_valid_postpone = False
                if req and req.start_time:
                    req_time = (
                        req.start_time.replace(tzinfo=None)
                        if req.start_time.tzinfo is not None
                        else req.start_time
                    )
                    if now_naive <= req_time:
                        has_valid_postpone = True

                if has_valid_postpone:
                    logger.info(
                        f"User {user_id} chưa xong bài tập '{homework.title}' nhưng có đơn xin hoãn hợp lệ đến {req.start_time}. Bỏ qua vi phạm."
                    )
                    continue

                for ticket_type in uncompleted_types:
                    reason_msg = (
                        f"Chưa hoàn thành bài tập {ticket_type} ({homework.title}) quá thời gian xin hẹn"
                        if req
                        else f"Chưa hoàn thành bài tập {ticket_type} ({homework.title}) và không phép"
                    )

                    await self.event_bus.publish(
                        cast(
                            DomainEvent,
                            HomeworkOverdueDetected(
                                user_id=user_id,
                                homework_id=homework.id,
                                homework_title=homework.title,
                                deadline_date=str(homework.deadline.date()),
                                reason=reason_msg,
                            ),
                        )
                    )
                    created_violations_count += 1

        return created_violations_count
