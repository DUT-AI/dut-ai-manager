import asyncio
from loguru import logger

from app.homework.application.dtos import HomeworkReportResponse, HomeworkResponse
from app.homework.application.helpers import QuizSubmissionHelper
from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.homework.infrastructure.repository import HomeworkRepository
from app.shared.domain.query_support import QuerySupport
from app.shared.domain.value_objects import UserRef
from app.user.infrastructure.repository import UserRepository
from app.utils.datetime import get_current_utc7_time


class GetHomeworksUseCase:
    """Query homeworks with query support & assigned user / submission filtering."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        quiz_api: QuizApiClient,
        user_repo: UserRepository,
    ):
        self.homework_repo = homework_repo
        self.quiz_api = quiz_api
        self.user_repo = user_repo

    def get_all(
        self, skip: int = 0, limit: int = 100, deleted: bool = False
    ) -> list[HomeworkEntity]:
        return self.homework_repo.get_all(skip=skip, limit=limit, deleted=deleted)

    async def get_assigned_to_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[HomeworkResponse]:
        all_homeworks = self.homework_repo.get_all(skip=0, limit=1000)
        assigned_homeworks: list[HomeworkEntity] = []
        for hw in all_homeworks:
            if not hw.id:
                continue
            if user_id in (hw.assignee_ids or []):
                assigned_homeworks.append(hw)

        paged_hw = assigned_homeworks[skip : skip + limit]
        if not paged_hw:
            return []

        now = get_current_utc7_time()

        # Parallel fetch quiz status for these slugs
        slugs_set: set[str] = set()
        for hw in paged_hw:
            s = QuizSubmissionHelper.extract_slug_from_entity(hw)
            if s:
                slugs_set.add(s)

        coding_cache: dict[str, set[int] | None] = {}
        game_cache: dict[str, set[int] | None] = {}

        if slugs_set:
            async def fetch_coding(slug: str):
                coding_cache[slug] = (
                    await QuizSubmissionHelper.get_coding_completed_user_ids(
                        self.quiz_api, slug
                    )
                )

            async def fetch_game(slug: str):
                game_cache[slug] = (
                    await QuizSubmissionHelper.get_game_completed_user_ids(
                        self.quiz_api, slug
                    )
                )

            tasks = []
            for slug in slugs_set:
                tasks.append(fetch_coding(slug))
                tasks.append(fetch_game(slug))
            await asyncio.gather(*tasks)

        responses: list[HomeworkResponse] = []
        for hw in paged_hw:
            assert hw.id is not None
            slug = QuizSubmissionHelper.extract_slug_from_entity(hw)
            coding_uids = coding_cache.get(slug) if slug else None
            game_uids = game_cache.get(slug) if slug else None

            has_coding = coding_uids is not None
            coding_submitted = (
                (user_id in coding_uids) if coding_uids is not None else False
            )
            has_game = game_uids is not None
            game_submitted = (
                (user_id in game_uids) if game_uids is not None else False
            )

            is_submitted = QuizSubmissionHelper.is_user_submitted(
                user_id, coding_uids, game_uids
            )
            is_overdue = not is_submitted and (hw.deadline < now)

            uncompleted: list[str] = []
            if has_coding and not coding_submitted:
                uncompleted.append("Bài tập Coding")
            if has_game and not game_submitted:
                uncompleted.append("Trắc nghiệm Game")

            resp = HomeworkResponse(
                id=hw.id,
                title=hw.title,
                deadline=hw.deadline,
                link=hw.link,
                slug=hw.slug,
                created_at=hw.created_at,
                updated_at=hw.updated_at,
                created_by=hw.created_by,
                assignee_ids=hw.assignee_ids or [],
                is_submitted=is_submitted,
                is_overdue=is_overdue,
                has_coding=has_coding,
                coding_submitted=coding_submitted,
                has_game=has_game,
                game_submitted=game_submitted,
                uncompleted_items=uncompleted,
            )
            responses.append(resp)

        return responses

    def get_by_id(self, homework_id: int) -> HomeworkEntity | None:
        return self.homework_repo.get_by_id(homework_id)

    def get_query_support(
        self, query_support: QuerySupport, deleted: bool = False
    ) -> list[HomeworkEntity]:
        return self.homework_repo.get_all(query_support=query_support, deleted=deleted)

    async def get_unsubmitted_for_user(self, user_id: int) -> list[HomeworkEntity]:
        """Lấy danh sách bài tập chưa nộp của user_id (kiểm tra Quiz API hoặc DB vi phạm)."""
        all_homeworks = self.homework_repo.get_all()
        now = get_current_utc7_time()

        # 1. Pre-filter homeworks assigned to target user_id
        assigned_homeworks = [
            hw for hw in all_homeworks if hw.id and user_id in (hw.assignee_ids or [])
        ]

        if not assigned_homeworks:
            return []

        # 2. Extract unique slugs only for assigned homeworks
        slugs_set: set[str] = set()
        for hw in assigned_homeworks:
            s = QuizSubmissionHelper.extract_slug_from_entity(hw)
            if s:
                slugs_set.add(s)
        unique_slugs: list[str] = list(slugs_set)

        coding_completed_cache: dict[str, set[int]] = {}
        game_completed_cache: dict[str, set[int]] = {}

        # 3. Fetch Quiz API status in parallel via asyncio.gather
        if unique_slugs:

            async def fetch_coding(slug: str):
                uids = await QuizSubmissionHelper.get_coding_completed_user_ids(
                    self.quiz_api, slug
                )
                if uids is not None:
                    coding_completed_cache[slug] = uids

            async def fetch_game(slug: str):
                uids = await QuizSubmissionHelper.get_game_completed_user_ids(
                    self.quiz_api, slug
                )
                if uids is not None:
                    game_completed_cache[slug] = uids

            tasks = []
            for slug in unique_slugs:
                tasks.append(fetch_coding(slug))
                tasks.append(fetch_game(slug))
            await asyncio.gather(*tasks)

        # 4. Determine unsubmitted homeworks
        unsubmitted: list[HomeworkEntity] = []
        for hw in assigned_homeworks:
            slug = QuizSubmissionHelper.extract_slug_from_entity(hw)

            if slug:
                coding_set = coding_completed_cache.get(slug, set())
                game_set = game_completed_cache.get(slug, set())

                if not QuizSubmissionHelper.is_user_submitted(user_id, coding_set, game_set):
                    unsubmitted.append(hw)
            else:
                if hw.deadline and hw.deadline < now:
                    unsubmitted.append(hw)

        return unsubmitted

    async def get_unsubmitted_report(self) -> list[HomeworkReportResponse]:
        """Thống kê tổng hợp số bài tập chưa nộp của toàn bộ user đang hoạt động."""
        active_users = self.user_repo.get_active_users()
        if not active_users:
            return []

        all_homeworks = self.homework_repo.get_all()

        # 1. Thu thập slug duy nhất
        slugs_set: set[str] = set()
        for hw in all_homeworks:
            s = QuizSubmissionHelper.extract_slug_from_entity(hw)
            if s:
                slugs_set.add(s)
        unique_slugs = list(slugs_set)

        coding_cache: dict[str, set[int] | None] = {}
        game_cache: dict[str, set[int] | None] = {}

        if unique_slugs:
            async def fetch_coding(s: str):
                coding_cache[s] = await QuizSubmissionHelper.get_coding_completed_user_ids(self.quiz_api, s)

            async def fetch_game(s: str):
                game_cache[s] = await QuizSubmissionHelper.get_game_completed_user_ids(self.quiz_api, s)

            tasks = []
            for s in unique_slugs:
                tasks.append(fetch_coding(s))
                tasks.append(fetch_game(s))
            await asyncio.gather(*tasks)

        # 2. Duyệt qua từng user và đếm số bài chưa nộp
        reports: list[HomeworkReportResponse] = []
        for user in active_users:
            if not user.id:
                continue
            uid = user.id
            unsubmitted_count = 0

            for hw in all_homeworks:
                if not hw.id:
                    continue
                if uid not in (hw.assignee_ids or []):
                    continue

                slug = QuizSubmissionHelper.extract_slug_from_entity(hw)
                if slug:
                    coding_uids = coding_cache.get(slug)
                    game_uids = game_cache.get(slug)
                    if not QuizSubmissionHelper.is_user_submitted(uid, coding_uids, game_uids):
                        unsubmitted_count += 1
                else:
                    # Bài tập thường nếu quá hạn
                    pass

            reports.append(
                HomeworkReportResponse(
                    user_id=uid,
                    owner=UserRef(
                        id=user.id,
                        name=user.name,
                        email=user.email,
                        avatar_url=user.avatar_url,
                    ),
                    unsubmitted_count=unsubmitted_count,
                )
            )

        # Sắp xếp số bài chưa nộp nhiều nhất lên trước
        reports.sort(key=lambda r: r.unsubmitted_count, reverse=True)
        return reports

