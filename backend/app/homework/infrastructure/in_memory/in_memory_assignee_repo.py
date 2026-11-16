from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from app.homework.domain.ports import HomeworkAssigneeRepositoryPort
from app.homework.domain.value_objects import (
    AssigneeUserInfo,
    DueHomeworkAssignment,
)
from app.shared.domain.datetime_types import ensure_utc


class InMemoryHomeworkAssigneeRepository(HomeworkAssigneeRepositoryPort):
    """Cài đặt In-Memory của HomeworkAssigneeRepositoryPort phục vụ kiểm thử nhanh và độc lập."""

    def __init__(self) -> None:
        # Key: (homework_id, user_id), Value: deadline (timezone-aware UTC)
        self._assignees: dict[tuple[int, int], datetime] = {}
        # Metadata phục vụ join: user_id -> (name, avatar_url)
        self._user_info: dict[int, tuple[str, str | None]] = {}
        # Metadata bài tập: homework_id -> (title, req_coding, req_game, slug)
        self._hw_info: dict[int, tuple[str, bool, bool, str]] = {}

    def clear(self) -> None:
        """Xóa toàn bộ phân công trong RAM."""
        self._assignees.clear()
        self._user_info.clear()
        self._hw_info.clear()

    def count(self) -> int:
        return len(self._assignees)

    def set_custom_deadline(
        self, homework_id: int, user_id: int, deadline: datetime
    ) -> None:
        """Helper thiết lập hạn nộp cá nhân cụ thể cho học viên."""
        self._assignees[(homework_id, user_id)] = ensure_utc(deadline)

    def set_user_info(self, user_id: int, name: str, avatar_url: str | None = None) -> None:
        self._user_info[user_id] = (name, avatar_url)

    def set_homework_info(
        self,
        homework_id: int,
        title: str,
        requires_coding: bool = True,
        requires_game: bool = False,
        slug: str = "",
    ) -> None:
        self._hw_info[homework_id] = (title, requires_coding, requires_game, slug)

    def set_assignees(
        self,
        homework_id: int,
        assignees: list[AssigneeUserInfo],
        default_deadline: datetime | None = None,
    ) -> None:
        """Helper fixture cho testing: thiết lập assignees trực tiếp kèm deadline."""
        for a in assignees:
            dl = a.deadline or default_deadline or datetime.now(UTC)
            self._assignees[(homework_id, a.user_id)] = ensure_utc(dl)
            if a.name:
                self.set_user_info(a.user_id, a.name, a.avatar_url)

    def sync_assignees(
        self,
        homework_id: int,
        assignee_ids: list[int] | None,
        default_deadline: datetime | None = None,
        force_override: bool = False,
    ) -> None:
        if assignee_ids is None:
            return

        current_assignees = {
            uid: dl
            for (hid, uid), dl in self._assignees.items()
            if hid == homework_id
        }
        new_uids = set(assignee_ids)

        # Xóa những học viên không còn trong danh sách
        for uid in list(current_assignees.keys()):
            if uid not in new_uids:
                del self._assignees[(homework_id, uid)]

        added_uids = [uid for uid in new_uids if uid not in current_assignees]
        clean_dl = self._resolve_clean_deadline(
            homework_id, added_uids, default_deadline, current_assignees
        )

        for uid in new_uids:
            if uid in current_assignees:
                if default_deadline is not None:
                    target_dl = ensure_utc(default_deadline)
                    curr_dl = current_assignees[uid]
                    if force_override or target_dl > curr_dl:
                        self._assignees[(homework_id, uid)] = target_dl
            else:
                assert clean_dl is not None
                self._assignees[(homework_id, uid)] = clean_dl

    def _resolve_clean_deadline(
        self,
        homework_id: int,
        added_uids: list[int],
        default_deadline: datetime | None,
        current_assignees: dict[int, datetime],
    ) -> datetime | None:
        if not added_uids:
            return None
        if default_deadline is not None:
            return ensure_utc(default_deadline)
        if current_assignees:
            return min(current_assignees.values())
        raise ValueError(
            f"Không thể gán học viên vào bài tập {homework_id} khi thiếu deadline"
        )

    def assign_users(
        self,
        homework_id: int,
        user_ids: set[int] | list[int],
        deadline: datetime,
        force_override: bool = False,
    ) -> None:
        clean_deadline = ensure_utc(deadline)
        for uid in user_ids:
            key = (homework_id, uid)
            if key in self._assignees and not force_override:
                curr = self._assignees[key]
                if clean_deadline > curr:
                    self._assignees[key] = clean_deadline
            else:
                self._assignees[key] = clean_deadline

    def get_user_deadline(
        self, homework_id: int, user_id: int
    ) -> datetime | None:
        return self._assignees.get((homework_id, user_id))

    def update_deadline(
        self, homework_id: int, user_id: int, new_deadline: datetime
    ) -> bool:
        key = (homework_id, user_id)
        if key in self._assignees:
            self._assignees[key] = ensure_utc(new_deadline)
            return True
        return False

    def get_by_deadline_date(
        self, target_date: date
    ) -> list[DueHomeworkAssignment]:
        results: list[DueHomeworkAssignment] = []
        vn_tz = ZoneInfo("Asia/Ho_Chi_Minh")
        for (hid, uid), dl in self._assignees.items():
            dl_local_date = dl.astimezone(vn_tz).date()
            if dl_local_date == target_date:
                title, req_coding, req_game, slug = self._hw_info.get(
                    hid, (f"Homework #{hid}", True, False, "")
                )
                results.append(
                    DueHomeworkAssignment(
                        homework_id=hid,
                        user_id=uid,
                        homework_title=title,
                        deadline=dl,
                        requires_coding=req_coding,
                        requires_game=req_game,
                        slug=slug,
                    )
                )
        return results

    def get_assigned_user_ids(self, homework_id: int) -> set[int]:
        return {uid for (hid, uid) in self._assignees if hid == homework_id}

    def get_assignees_with_user_info(
        self, homework_id: int
    ) -> list[AssigneeUserInfo]:
        res: list[AssigneeUserInfo] = []
        for (hid, uid), dl in self._assignees.items():
            if hid == homework_id:
                name, avatar = self._user_info.get(uid, (f"User #{uid}", None))
                res.append(
                    AssigneeUserInfo(
                        user_id=uid,
                        name=name,
                        avatar_url=avatar,
                        deadline=dl,
                    )
                )
        return res

    def get_assigned_homework_ids(self, user_id: int) -> list[int]:
        return [hid for (hid, uid) in self._assignees if uid == user_id]

    def get_user_deadlines_for_homeworks(
        self, user_id: int, homework_ids: list[int]
    ) -> dict[int, datetime | None]:
        return {
            hid: self._assignees.get((hid, user_id))
            for hid in homework_ids
        }

    def get_min_deadlines_by_homework_ids(
        self, homework_ids: list[int]
    ) -> dict[int, datetime | None]:
        res: dict[int, datetime | None] = dict.fromkeys(homework_ids)
        for (hid, _uid), dl in self._assignees.items():
            if hid in res:
                if res[hid] is None or dl < res[hid]:
                    res[hid] = dl
        return res

    def add_assignees(
        self, homework_id: int, user_ids: list[int], deadline: datetime
    ) -> None:
        self.assign_users(homework_id, user_ids, deadline)

    def remove_assignees(
        self, homework_id: int, user_ids: list[int]
    ) -> None:
        for uid in user_ids:
            self._assignees.pop((homework_id, uid), None)

    def get_distinct_past_deadline_dates(
        self, before_date: date
    ) -> list[date]:
        dates = set()
        vn_tz = ZoneInfo("Asia/Ho_Chi_Minh")
        for dl in self._assignees.values():
            d = dl.astimezone(vn_tz).date()
            if d < before_date:
                dates.add(d)
        return sorted(dates)
