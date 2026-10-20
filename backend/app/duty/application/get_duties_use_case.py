"""
Get Duties Use Case.
"""

from collections import defaultdict
from datetime import date, timedelta, time
from typing import Any

from app.duty.application.dtos import DutyResponse, WeeklyDutyClassDto
from app.duty.domain.entity import CleaningDuty, DutyStatus
from app.duty.infrastructure.repository import DutyRepository
from app.meeting.infrastructure.repository import MeetingRepository
from app.team.infrastructure.repository import TeamRepository


class GetDutiesUseCase:
    def __init__(
        self,
        repo: DutyRepository,
        team_repo: TeamRepository,
        meeting_repo: MeetingRepository,
    ):
        self.repo = repo
        self.team_repo = team_repo
        self.meeting_repo = meeting_repo

    def get_by_id(self, duty_id: int) -> DutyResponse | None:
        entity = self.repo.get_by_id(duty_id)
        if not entity:
            return None
        teams = self.team_repo.get_all_with_members()
        team_by_id = {t.id: t for t in teams if t.id}
        t_ids = entity.team_id if isinstance(entity.team_id, list) else [entity.team_id]
        t_names = [team_by_id[t].team_name for t in t_ids if t in team_by_id]
        entity.team_names = t_names
        entity.team_name = ", ".join(t_names) if t_names else entity.team_name
        return DutyResponse.model_validate(entity)

    def execute(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        team_id: int | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[DutyResponse], int]:
        entities, total = self.repo.get_duties(
            start_date=start_date,
            end_date=end_date,
            team_id=team_id,
            status=status,
            page=page,
            page_size=page_size,
        )
        teams = self.team_repo.get_all_with_members()
        team_by_id = {t.id: t for t in teams if t.id}
        for e in entities:
            t_ids = e.team_id if isinstance(e.team_id, list) else [e.team_id]
            t_names = [team_by_id[t].team_name for t in t_ids if t in team_by_id]
            e.team_names = t_names
            e.team_name = ", ".join(t_names) if t_names else e.team_name

        return [DutyResponse.model_validate(e) for e in entities], total

    def get_weekly_schedule(self, target_date: date | None = None) -> list[WeeklyDutyClassDto]:
        """
        Lấy lịch trực nhật động trong tuần:
        - Tự động lấy tất cả các buổi Meeting thực tế trong tuần (thay đổi giờ, ngày linh hoạt).
        - Bao gồm các ca trực nhật tự do do Admin/HR tạo (không ràng buộc bởi meeting).
        """
        if not target_date:
            target_date = date.today()

        # Tìm thứ 2 và chủ nhật trong tuần
        monday = target_date - timedelta(days=target_date.weekday())
        sunday = monday + timedelta(days=6)

        # Lấy tất cả meeting và duty trong tuần
        meetings = self.meeting_repo.get_by_date_range(monday, sunday)
        duties = self.repo.get_by_date_range(monday, sunday)
        teams = self.team_repo.get_all_with_members()

        team_by_id = {t.id: t for t in teams if t.id}
        team_users = {
            t.id: {m.user_id for m in t.members if m.user_id} for t in teams if t.id
        }

        # Tập hợp các nhóm Gen 2 (phụ trách trực nhật văn phòng)
        gen2_teams = [
            t
            for t in teams
            if t.id
            and (
                "gen 2" in (t.team_name or "").lower()
                or "gen2" in (t.team_name or "").lower()
            )
        ]
        # Mapping thứ trong tuần -> team Gen 2 tương ứng
        gen2_by_weekday: dict[int, Any] = {}
        for t in gen2_teams:
            tn = (t.team_name or "").lower()
            if "thứ 3" in tn or "thu 3" in tn:
                gen2_by_weekday[1] = t
            elif "thứ 4" in tn or "thu 4" in tn:
                gen2_by_weekday[2] = t
            elif "thứ 5" in tn or "thu 5" in tn:
                gen2_by_weekday[3] = t
            elif "thứ 7" in tn or "thu 7" in tn:
                gen2_by_weekday[5] = t

        all_gen2_user_ids = set()
        for gt in gen2_teams:
            all_gen2_user_ids.update(team_users.get(gt.id, set()))

        # Gom danh sách duties theo meeting_id
        duties_by_meeting: dict[int, list[CleaningDuty]] = defaultdict(list)
        duty_by_date_team: dict[tuple[date, int], CleaningDuty] = {}
        for d in duties:
            if d.meeting_id:
                duties_by_meeting[d.meeting_id].append(d)
            t_ids = d.team_id if isinstance(d.team_id, list) else [d.team_id]
            for tid in t_ids:
                duty_by_date_team[(d.duty_date, tid)] = d

        processed_duty_ids: set[int] = set()
        results: list[WeeklyDutyClassDto] = []
        day_names = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]

        # 1. Quét theo các buổi Meeting thực tế trong tuần của Gen 2
        for m in meetings:
            m_date = m.start_time.date()
            day_idx = m_date.weekday()
            day_name = day_names[day_idx]
            meeting_time = (
                f"{m.start_time.strftime('%H:%M')} - {m.end_time.strftime('%H:%M')}"
            )
            m_title_lower = (m.title or "").lower()
            p_ids = {p.user_id for p in m.participants if not p.is_deleted} if m.participants else set()

            # Kiểm tra xem meeting có phải của Gen 2 hay thuần Gen 1
            has_gen2_participants = bool(p_ids & all_gen2_user_ids)
            is_gen2_title = ("gen 2" in m_title_lower) or ("gen2" in m_title_lower)
            is_gen1_title = ("gen 1" in m_title_lower) or ("gen1" in m_title_lower)

            # 1. Nếu tiêu đề nói rõ Gen 1 mà không có Gen 2 -> Bỏ qua
            if is_gen1_title and not is_gen2_title and not has_gen2_participants:
                continue

            # 2. Nếu meeting có người tham gia nhưng 100% là Gen 1 (không có ai thuộc Gen 2) và tiêu đề không phải Gen 2 -> Bỏ qua
            if p_ids and not has_gen2_participants and not is_gen2_title:
                continue

            # Ưu tiên tìm ca trực đã gắn với meeting này
            m_duties = duties_by_meeting.get(m.id, [])
            duty: CleaningDuty | None = None
            if m_duties:
                # Ưu tiên lấy duty active: PENDING, AWAITING_APPROVAL, REJECTED
                active_duties = [
                    d for d in m_duties
                    if d.status in [DutyStatus.PENDING, DutyStatus.AWAITING_APPROVAL, DutyStatus.REJECTED]
                ]
                if active_duties:
                    duty = active_duties[0]
                else:
                    cancelled_duties = [d for d in m_duties if d.status == DutyStatus.CANCELLED]
                    if cancelled_duties:
                        duty = cancelled_duties[0]
                    else:
                        duty = m_duties[0]

            if duty:
                t_ids = duty.team_id if isinstance(duty.team_id, list) else [duty.team_id]
                t_names = [team_by_id[t].team_name for t in t_ids if t in team_by_id]
                team_name = ", ".join(t_names) if t_names else (duty.team_name or f"Nhóm #{t_ids}")
                team_id = t_ids
                team_names = t_names
            else:
                # Dò tìm nhóm Gen 2 phù hợp nhất cho buổi meeting
                best_team = None
                best_overlap = 0

                for t in gen2_teams:
                    overlap = len(p_ids & team_users.get(t.id, set()))
                    if overlap > best_overlap:
                        best_overlap = overlap
                        best_team = t
                    elif overlap == best_overlap and best_overlap > 0:
                        # Nếu overlap bằng nhau, ưu tiên team có thứ sinh hoạt trùng với thứ của meeting
                        if gen2_by_weekday.get(day_idx) == t:
                            best_team = t

                # Nếu không có overlap (meeting mở hoặc chưa gán participants), ưu tiên theo thứ sinh hoạt
                if not best_team:
                    best_team = gen2_by_weekday.get(day_idx)

                # Nếu vẫn chưa tìm được (ví dụ meeting vào Thứ 2 hoặc Thứ 6)
                if not best_team:
                    for t in gen2_teams:
                        tname_lower = (t.team_name or "").lower()
                        if any(k in m_title_lower for k in ["thứ 3", "thu 3"]) and ("thứ 3" in tname_lower or "thu 3" in tname_lower):
                            best_team = t
                            break
                        if any(k in m_title_lower for k in ["thứ 4", "thu 4"]) and ("thứ 4" in tname_lower or "thu 4" in tname_lower):
                            best_team = t
                            break
                        if any(k in m_title_lower for k in ["thứ 5", "thu 5"]) and ("thứ 5" in tname_lower or "thu 5" in tname_lower):
                            best_team = t
                            break
                        if any(k in m_title_lower for k in ["thứ 7", "thu 7"]) and ("thứ 7" in tname_lower or "thu 7" in tname_lower):
                            best_team = t
                            break

                # Fallback cuối cùng: chọn nhóm Gen 2 đầu tiên hoặc team 12
                if not best_team and gen2_teams:
                    best_team = gen2_teams[0]

                best_id = best_team.id if best_team and best_team.id else 12
                team_id = [best_id]
                team_name = best_team.team_name if best_team else f"Nhóm #{best_id}"
                team_names = [team_name]

                # Kiểm tra xem ngày đó đã có ca trực của team này chưa
                duty = duty_by_date_team.get((m_date, best_id))

            m_start = m.start_time.time() if m.start_time else None
            m_end = m.end_time.time() if m.end_time else None
            duty_start = duty.start_time if (duty and duty.start_time) else m_start
            duty_end = duty.end_time if (duty and duty.end_time) else m_end

            if duty and duty.id and duty.status != DutyStatus.CANCELLED:
                processed_duty_ids.add(duty.id)
                is_scheduled = True
                duty_status = duty.status.value
            else:
                if duty and duty.id:
                    processed_duty_ids.add(duty.id)
                is_scheduled = False
                duty_status = "NOT_SCHEDULED"

            results.append(
                WeeklyDutyClassDto(
                    team_id=team_id,
                    team_name=team_name,
                    team_names=team_names,
                    day_of_week=day_idx + 1,
                    day_name=day_name,
                    duty_date=m_date,
                    start_time=duty_start,
                    end_time=duty_end,
                    has_meeting=True,
                    meeting_id=m.id,
                    meeting_title=m.title,
                    meeting_time=meeting_time,
                    is_scheduled=is_scheduled,
                    duty_id=duty.id if duty else None,
                    status=duty_status,
                    evidence_image_urls=duty.evidence_image_urls if duty else [],
                    note=duty.note if duty else None,
                    checklist=duty.checklist if duty else [],
                    submitted_by_name=duty.submitted_by_name if duty else None,
                    rejection_reason=duty.rejection_reason if duty else None,
                )
            )

        # 2. Bổ sung các ca trực nhật tự do do Admin/HR tạo (không gắn với Meeting nào)
        for d in duties:
            if d.id in processed_duty_ids:
                continue
            day_idx = d.duty_date.weekday()
            day_name = day_names[day_idx]

            t_ids = d.team_id if isinstance(d.team_id, list) else [d.team_id]
            t_names = [
                team_by_id[t].team_name
                for t in t_ids
                if t in team_by_id and team_by_id[t].team_name
            ]
            team_name = ", ".join(t_names) if t_names else (d.team_name or f"Nhóm #{t_ids}")

            team_name_lower = (team_name or "").lower()
            if "gen 1" in team_name_lower or "gen1" in team_name_lower:
                continue

            # Nghiệp vụ: Ca trực đã COMPLETED thì không cần hiển thị ở Tab Lịch Tuần nữa
            if d.status == DutyStatus.COMPLETED:
                continue

            # Ca tự do: Nếu CANCELLED thì is_scheduled = False (switch OFF) và status = NOT_SCHEDULED
            is_scheduled = (d.status != DutyStatus.CANCELLED)
            duty_status = d.status.value if is_scheduled else "NOT_SCHEDULED"

            free_time_str = None
            if d.start_time and d.end_time:
                free_time_str = f"{d.start_time.strftime('%H:%M')} - {d.end_time.strftime('%H:%M')}"
            elif d.start_time:
                free_time_str = f"{d.start_time.strftime('%H:%M')}"

            results.append(
                WeeklyDutyClassDto(
                    team_id=t_ids,
                    team_name=team_name,
                    team_names=t_names,
                    day_of_week=day_idx + 1,
                    day_name=day_name,
                    duty_date=d.duty_date,
                    start_time=d.start_time,
                    end_time=d.end_time,
                    has_meeting=False,
                    meeting_id=None,
                    meeting_title=None,
                    meeting_time=free_time_str,
                    is_scheduled=is_scheduled,
                    duty_id=d.id,
                    status=duty_status,
                    evidence_image_urls=d.evidence_image_urls,
                    note=d.note,
                    checklist=d.checklist or [],
                    submitted_by_name=d.submitted_by_name,
                    rejection_reason=d.rejection_reason,
                )
            )

        # 3. Kiểm tra xung đột khung giờ trực nhật giữa các ca của cùng một nhóm trong ngày
        duties_by_date_and_team = defaultdict(list)
        for r in results:
            if r.is_scheduled and r.start_time:
                t_ids = r.team_id if isinstance(r.team_id, list) else [r.team_id]
                for tid in t_ids:
                    duties_by_date_and_team[(r.duty_date, tid)].append(r)

        for (_d_date, _t_id), items in duties_by_date_and_team.items():
            if len(items) > 1:
                for i in range(len(items)):
                    for j in range(i + 1, len(items)):
                        item_a = items[i]
                        item_b = items[j]
                        s_a, e_a = item_a.start_time, item_a.end_time
                        s_b, e_b = item_b.start_time, item_b.end_time

                        overlap = False
                        if s_a and e_a and s_b and e_b:
                            overlap = (s_a < e_b) and (s_b < e_a)
                        elif s_a and s_b:
                            overlap = (s_a == s_b)

                        if overlap:
                            item_a.is_time_conflict = True
                            time_b_str = (
                                f"{s_b.strftime('%H:%M')} - {e_b.strftime('%H:%M')}"
                                if (s_b and e_b)
                                else (s_b.strftime('%H:%M') if s_b else "")
                            )
                            item_a.conflict_message = (
                                f"Trùng khung giờ với ca trực khác ({time_b_str})"
                            )

                            item_b.is_time_conflict = True
                            time_a_str = (
                                f"{s_a.strftime('%H:%M')} - {e_a.strftime('%H:%M')}"
                                if (s_a and e_a)
                                else (s_a.strftime('%H:%M') if s_a else "")
                            )
                            item_b.conflict_message = (
                                f"Trùng khung giờ với ca trực khác ({time_a_str})"
                            )

        results.sort(
            key=lambda r: (
                r.duty_date,
                r.start_time or time(0, 0),
                r.team_id,
            )
        )
        return results
