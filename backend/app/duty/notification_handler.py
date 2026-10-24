import asyncio
from collections.abc import Callable
from datetime import date, datetime, time

from loguru import logger

from app.core.config import settings
from app.duty.domain.entity import CleaningDuty
from app.duty.domain.events import DutyScheduled, DutySubmitted, DutyUpdated
from app.duty.infrastructure.repository import DutyRepository
from app.meeting.domain.entity import Meeting
from app.meeting.domain.events import MeetingUpdated
from app.meeting.domain.value_objects import ParticipantStatus
from app.meeting.infrastructure.repository import MeetingRepository
from app.shared.application.event_handler import EventHandler
from app.shared.infrastructure.notification.dispatcher import (
    UnifiedNotificationDispatcher,
)
from app.shared.infrastructure.notification_payload import (
    NotificationCategory,
    NotificationLevel,
    NotificationPayload,
)
from app.permission_request.infrastructure.repository import (
    PermissionRequestRepository,
)
from app.team.infrastructure.repository import TeamRepository
from app.user.infrastructure.repository import UserRepository


class DutyNotificationHandler(EventHandler):
    """
    Xử lý gửi thông báo sự kiện Trực nhật:
    1. DutyScheduled: Gửi thông báo đến từng học viên khi lịch trực nhật được tạo/bật.
    2. DutySubmitted: Gửi thông báo lên room Discord khi học viên nộp minh chứng để Admin/HR duyệt.
    3. MeetingUpdated: Tự động cập nhật ca trực nhật và gửi thông báo mới khi lịch meeting thay đổi ngày/giờ.
    4. DutyUpdated: Gửi thông báo điều chỉnh thời gian ca trực tự do đến các học viên phụ trách.
    """

    def __init__(
        self,
        dispatcher: UnifiedNotificationDispatcher,
        user_repo: UserRepository,
        team_repo: TeamRepository,
        meeting_repo: MeetingRepository,
        duty_repo: DutyRepository,
        permission_repo: PermissionRequestRepository | None = None,
    ):
        self.dispatcher = dispatcher
        self.user_repo = user_repo
        self.team_repo = team_repo
        self.meeting_repo = meeting_repo
        self.duty_repo = duty_repo
        self.permission_repo = permission_repo

    async def handle(
        self, event: DutySubmitted | DutyScheduled | DutyUpdated | MeetingUpdated
    ) -> None:
        try:
            if isinstance(event, DutySubmitted):
                logger.info(f"Handling DutySubmitted for duty_id={event.duty_id}")
                asyncio.create_task(self._send_submitted_notification_task(event))
            elif isinstance(event, DutyScheduled):
                logger.info(f"Handling DutyScheduled for duty_id={event.duty_id}")
                asyncio.create_task(self._send_scheduled_notification_task(event))
            elif isinstance(event, DutyUpdated):
                logger.info(f"Handling DutyUpdated for duty_id={event.duty_id}")
                asyncio.create_task(self._send_duty_updated_notification_task(event))
            elif isinstance(event, MeetingUpdated):
                logger.info(
                    f"Handling MeetingUpdated for duty adjustment, meeting_id={event.meeting_id}"
                )
                asyncio.create_task(
                    self._send_meeting_rescheduled_notification_task(event)
                )
        except Exception as e:
            logger.error(f"Error in DutyNotificationHandler.handle: {e}")

    # ================= Shared Helper Methods =================

    @staticmethod
    def _format_date(d: date | str | None) -> str:
        """Định dạng ngày sang dd/mm/yyyy."""
        if not d:
            return ""
        if isinstance(d, str):
            try:
                return datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m/%Y")
            except ValueError:
                return d
        return d.strftime("%d/%m/%Y")

    @staticmethod
    def _format_time_range(
        start_t: time | None, end_t: time | None, fallback: str = "Theo phân công"
    ) -> str:
        """Định dạng khung giờ HH:MM – HH:MM."""
        if start_t and end_t:
            return f"{start_t.strftime('%H:%M')} – {end_t.strftime('%H:%M')}"
        if start_t:
            return f"Từ {start_t.strftime('%H:%M')}"
        return fallback

    def _extract_meeting_participant_ids(self, meeting: Meeting | None) -> list[int]:
        """
        Trích xuất ID các học viên hợp lệ từ buổi meeting:
        - Loại trừ người tạo/trainer.
        - Loại trừ học viên có đơn xin vắng (ABSENCE) hoặc đổi buổi chuyển đi (CHANGE_MEETING).
        - Loại trừ học viên có trạng thái vắng (ABSENT_EXCUSED, ABSENT_UNEXCUSED).
        - Bổ sung học viên đổi buổi chuyển ĐẾN meeting này.
        """
        if not meeting:
            return []

        excluded_user_ids: set[int] = set()
        creator_id = getattr(meeting, "created_by", None)
        if creator_id:
            excluded_user_ids.add(creator_id)

        # Lấy danh sách xin vắng hoặc đổi buổi chuyển đi từ permission_repo
        if self.permission_repo and meeting.id:
            excluded_user_ids.update(
                self.permission_repo.get_all_excused_or_transferred_out_user_ids(
                    meeting.id
                )
            )

        valid_ids: list[int] = []
        if meeting.participants:
            for p in meeting.participants:
                if getattr(p, "is_deleted", False):
                    continue
                if p.user_id in excluded_user_ids:
                    continue
                if p.status in (
                    ParticipantStatus.ABSENT_EXCUSED,
                    ParticipantStatus.ABSENT_UNEXCUSED,
                ):
                    continue
                valid_ids.append(p.user_id)

        # Bổ sung các bạn đổi buổi chuyển ĐẾN meeting này
        if self.permission_repo and meeting.id:
            transferred_in_ids = (
                self.permission_repo.get_transferred_in_user_ids_by_meeting(
                    meeting.id
                )
            )
            for uid in transferred_in_ids:
                if uid not in valid_ids and uid not in excluded_user_ids:
                    valid_ids.append(uid)

        return valid_ids

    def _extract_team_member_ids(self, team_ids: int | list[int]) -> list[int]:
        """Lấy tất cả member_id từ danh sách nhóm."""
        t_ids = team_ids if isinstance(team_ids, list) else [team_ids]
        member_ids: list[int] = []
        for t_id in t_ids:
            team = self.team_repo.get_by_id(t_id)
            if not team:
                continue
            if team.member_ids:
                member_ids.extend(team.member_ids)
            elif team.members:
                member_ids.extend(m.user_id for m in team.members if m.user_id)
            elif team.users:
                member_ids.extend(u.id for u in team.users if u.id)
        return member_ids

    def _resolve_target_user_ids(
        self,
        duty: CleaningDuty | None,
        meeting: Meeting | None,
        fallback_team_ids: int | list[int],
    ) -> list[int]:
        """Thu thập và deduplicate danh sách học viên cần gửi thông báo trực nhật."""
        candidate_ids = self._extract_meeting_participant_ids(meeting)
        if not candidate_ids:
            candidate_ids = self._extract_team_member_ids(fallback_team_ids)
            # Nếu có meeting gắn với ca trực, loại trừ các bạn vắng / đổi buổi
            if meeting and meeting.id and self.permission_repo:
                excluded = (
                    self.permission_repo.get_all_excused_or_transferred_out_user_ids(
                        meeting.id
                    )
                )
                candidate_ids = [uid for uid in candidate_ids if uid not in excluded]

        return list(dict.fromkeys(candidate_ids))

    async def _dispatch_to_users(
        self,
        user_ids: list[int],
        title: str,
        content_generator: Callable[[str], str],
        fields: list[dict],
        action_url: str = "/dashboard/duties",
    ) -> None:
        """Phát thông báo đồng loạt tới danh sách học viên qua UnifiedNotificationDispatcher."""
        full_url = (
            f"{settings.FRONTEND_URL}{action_url}"
            if not action_url.startswith("http")
            else action_url
        )

        for uid in user_ids:
            user = self.user_repo.get_by_id(uid)
            user_name = user.name if user else f"Thành viên #{uid}"
            payload = NotificationPayload(
                user_id=uid,
                title=title,
                content=content_generator(user_name),
                category=NotificationCategory.DUTY,
                level=NotificationLevel.INFO,
                image_asset="meme-lam-viec.webp",
                fields=fields,
                action_url=full_url,
            )
            await self.dispatcher.dispatch(payload)

    def _resolve_gen2_team_name(
        self,
        linked_duties: list[CleaningDuty],
        gen2_teams: list,
        team_users: dict[int, set[int]],
        p_ids: set[int],
        new_date: date,
    ) -> str:
        """Xác định tên nhóm Gen 2 tương ứng dựa trên ca trực linked, overlap học viên hoặc ngày trong tuần."""
        if linked_duties and linked_duties[0].team_name:
            return linked_duties[0].team_name
        if linked_duties and linked_duties[0].team_id:
            t_ids = (
                linked_duties[0].team_id
                if isinstance(linked_duties[0].team_id, list)
                else [linked_duties[0].team_id]
            )
            t_names = [
                t.team_name for tid in t_ids if (t := self.team_repo.get_by_id(tid))
            ]
            return ", ".join(t_names) if t_names else f"Nhóm #{t_ids}"

        best_team = None
        best_overlap = 0
        for t in gen2_teams:
            overlap = len(p_ids & team_users.get(t.id, set()))
            if overlap > best_overlap:
                best_overlap = overlap
                best_team = t

        if not best_team:
            day_map = {
                1: ["thứ 3", "thu 3"],
                2: ["thứ 4", "thu 4"],
                3: ["thứ 5", "thu 5"],
                5: ["thứ 7", "thu 7"],
            }
            day_idx = new_date.weekday()
            for t in gen2_teams:
                tn = (t.team_name or "").lower()
                if day_idx in day_map and any(kw in tn for kw in day_map[day_idx]):
                    best_team = t
                    break

        if not best_team and gen2_teams:
            best_team = gen2_teams[0]

        return best_team.team_name if best_team else "Nhóm Gen 2"

    # ================= Task Handlers =================

    async def _send_scheduled_notification_task(self, event: DutyScheduled) -> None:
        """Gửi thông báo phân công ca trực nhật tới học viên."""
        try:
            duty = self.duty_repo.get_by_id(event.duty_id)
            meeting_id = event.meeting_id or (duty.meeting_id if duty else None)
            meeting = self.meeting_repo.get_by_id(meeting_id) if meeting_id else None
            if not meeting and duty and duty.duty_date:
                meetings = self.meeting_repo.get_by_date(duty.duty_date)
                if meetings:
                    meeting = meetings[0]

            target_user_ids = self._resolve_target_user_ids(
                duty=duty, meeting=meeting, fallback_team_ids=event.team_id
            )
            if not target_user_ids:
                logger.warning(
                    f"No participants or team members found to notify for duty_id={event.duty_id}"
                )
                return

            duty_date_str = self._format_date(event.duty_date)
            time_str = "Theo lịch sinh hoạt phòng Lab"
            if duty and (duty.start_time or duty.end_time):
                time_str = self._format_time_range(duty.start_time, duty.end_time)
            elif meeting and (meeting.start_time or meeting.end_time):
                s_time = (
                    meeting.start_time.time()
                    if hasattr(meeting.start_time, "time")
                    else None
                )
                e_time = (
                    meeting.end_time.time()
                    if hasattr(meeting.end_time, "time")
                    else None
                )
                time_str = self._format_time_range(s_time, e_time)

            title = "🧹 [TRỰC NHẬT] PHÂN CÔNG TRỰC NHẬT PHÒNG LAB"
            fields = [
                {"name": "👥 Nhóm phụ trách", "value": event.team_name, "inline": True},
                {"name": "📅 Ngày trực", "value": duty_date_str, "inline": True},
                {"name": "⏰ Khung giờ trực", "value": time_str, "inline": True},
            ]
            if duty and duty.note:
                fields.append(
                    {
                        "name": "📝 Ghi chú phân công",
                        "value": duty.note,
                        "inline": False,
                    }
                )
            fields.append(
                {
                    "name": "📌 Lưu ý quan trọng",
                    "value": "Vui lòng quét dọn, lau bàn ghế, sàn phòng Lab và nộp ảnh minh chứng thành phẩm trước 22:00 cùng ngày để tránh bị phạt vi phạm.",
                    "inline": False,
                }
            )

            def build_content(user_name: str) -> str:
                return (
                    f"Chào **{user_name}**!\n"
                    f"Bạn có lịch phân công trực nhật phòng Lab cho **{event.team_name}** "
                    f"vào ngày **{duty_date_str}** ({time_str}).\n"
                    f"👉 Vui lòng dọn dẹp vệ sinh phòng Lab và nộp ảnh minh chứng lên hệ thống."
                )

            await self._dispatch_to_users(
                user_ids=target_user_ids,
                title=title,
                content_generator=build_content,
                fields=fields,
            )
            logger.info(
                f"Successfully sent duty schedule notifications to {len(target_user_ids)} users for duty_id={event.duty_id}"
            )
        except Exception as e:
            logger.error(f"Error in _send_scheduled_notification_task: {e}")

    async def _send_meeting_rescheduled_notification_task(
        self, event: MeetingUpdated
    ) -> None:
        """Tự động đồng bộ ca trực nhật và gửi thông báo mới khi meeting đổi lịch."""
        try:
            start_dt = datetime.fromisoformat(event.start_time)
            end_dt = datetime.fromisoformat(event.end_time)
            new_date = start_dt.date()
            new_start_time = start_dt.time()
            new_end_time = end_dt.time()
            duty_date_str = new_date.strftime("%d/%m/%Y")
            time_str = (
                f"{new_start_time.strftime('%H:%M')} – {new_end_time.strftime('%H:%M')}"
            )

            # 1. Tự động đồng bộ các ca trực gắn với meeting trong DB
            linked_duties = self.duty_repo.get_by_meeting_id(event.meeting_id)
            for d in linked_duties:
                d.duty_date = new_date
                d.start_time = new_start_time
                d.end_time = new_end_time
                self.duty_repo.save(d)

            # 2. Thu thập danh sách học viên cần thông báo
            meeting = self.meeting_repo.get_by_id(event.meeting_id)
            candidate_user_ids = self._extract_meeting_participant_ids(meeting)
            if not candidate_user_ids and event.user_ids:
                excluded_user_ids: set[int] = set()
                if self.permission_repo and event.meeting_id:
                    excluded_user_ids.update(
                        self.permission_repo.get_all_excused_or_transferred_out_user_ids(
                            event.meeting_id
                        )
                    )
                candidate_user_ids = [
                    uid for uid in event.user_ids if uid not in excluded_user_ids
                ]

            p_ids = set(candidate_user_ids)
            teams = self.team_repo.get_all_with_members()
            gen2_teams = [
                t
                for t in teams
                if t.id
                and any(kw in (t.team_name or "").lower() for kw in ["gen 2", "gen2"])
            ]
            team_users = {
                t.id: {m.user_id for m in t.members if m.user_id} for t in teams if t.id
            }
            all_gen2_user_ids = set().union(
                *[team_users.get(gt.id, set()) for gt in gen2_teams]
            )

            title_lower = (event.title or "").lower()
            is_gen2_title = any(kw in title_lower for kw in ["gen 2", "gen2"])
            has_gen2_participants = bool(p_ids & all_gen2_user_ids)

            # Bỏ qua nếu là meeting thuần Gen 1
            if p_ids and not has_gen2_participants and not is_gen2_title:
                logger.info(
                    f"Meeting {event.meeting_id} is pure Gen 1, skipping duty reschedule notification"
                )
                return

            team_name = self._resolve_gen2_team_name(
                linked_duties=linked_duties,
                gen2_teams=gen2_teams,
                team_users=team_users,
                p_ids=p_ids,
                new_date=new_date,
            )

            target_user_ids = list(dict.fromkeys(candidate_user_ids))
            if not target_user_ids:
                logger.warning(
                    f"No participants to notify for rescheduled meeting_id={event.meeting_id}"
                )
                return

            title = "🧹 [ĐIỀU CHỈNH LỊCH TRỰC NHẬT] THAY ĐỔI THEO LỊCH MEETING"
            fields = [
                {"name": "👥 Nhóm phụ trách", "value": team_name, "inline": True},
                {"name": "📅 Ngày trực mới", "value": duty_date_str, "inline": True},
                {"name": "⏰ Giờ trực mới", "value": time_str, "inline": True},
                {
                    "name": "📌 Lý do điều chỉnh",
                    "value": f"Buổi meeting '{event.title}' vừa thay đổi thời gian tổ chức.",
                    "inline": False,
                },
                {
                    "name": "⚠️ Lưu ý",
                    "value": "Lịch trực nhật phòng Lab tự động điều chỉnh theo khung giờ meeting mới. Vui lòng sắp xếp dọn dẹp và nộp minh chứng trước 22:00 cùng ngày.",
                    "inline": False,
                },
            ]

            def build_content(user_name: str) -> str:
                return (
                    f"Chào **{user_name}**!\n"
                    f"Buổi sinh hoạt **'{event.title}'** đã thay đổi thời gian, "
                    f"lịch trực nhật phòng Lab của **{team_name}** được điều chỉnh tương ứng sang:\n"
                    f"📅 **Ngày trực mới**: {duty_date_str}\n"
                    f"⏰ **Khung giờ mới**: {time_str}\n"
                    f"👉 Vui lòng lưu ý khung giờ mới để trực nhật và nộp ảnh minh chứng đúng hạn."
                )

            await self._dispatch_to_users(
                user_ids=target_user_ids,
                title=title,
                content_generator=build_content,
                fields=fields,
            )
            logger.info(
                f"Successfully sent duty rescheduled notifications to {len(target_user_ids)} users for meeting_id={event.meeting_id}"
            )
        except Exception as e:
            logger.error(f"Error in _send_meeting_rescheduled_notification_task: {e}")

    async def _send_duty_updated_notification_task(self, event: DutyUpdated) -> None:
        """Gửi thông báo cập nhật thời gian ca trực tự do."""
        try:
            duty = self.duty_repo.get_by_id(event.duty_id)
            meeting = (
                self.meeting_repo.get_by_id(duty.meeting_id)
                if (duty and duty.meeting_id)
                else None
            )

            target_user_ids = self._resolve_target_user_ids(
                duty=duty, meeting=meeting, fallback_team_ids=event.team_id
            )
            if not target_user_ids:
                logger.warning(
                    f"No users to notify for updated duty_id={event.duty_id}"
                )
                return

            duty_date_str = self._format_date(event.duty_date)
            time_str = "Theo phân công của Admin/HR"
            if duty and (duty.start_time or duty.end_time):
                time_str = self._format_time_range(duty.start_time, duty.end_time)

            title = "🧹 [CẬP NHẬT LỊCH TRỰC NHẬT] ĐIỀU CHỈNH THỜI GIAN TRỰC"
            fields = [
                {"name": "👥 Nhóm phụ trách", "value": event.team_name, "inline": True},
                {"name": "📅 Ngày trực mới", "value": duty_date_str, "inline": True},
                {"name": "⏰ Giờ trực mới", "value": time_str, "inline": True},
            ]
            if duty and duty.note:
                fields.append(
                    {
                        "name": "📝 Ghi chú phân công",
                        "value": duty.note,
                        "inline": False,
                    }
                )
            fields.append(
                {
                    "name": "📌 Lưu ý",
                    "value": "Lịch trực nhật đã được cập nhật lại. Vui lòng lưu ý thời gian mới để hoàn thành trực nhật và nộp ảnh minh chứng đúng hạn trước 22:00 cùng ngày.",
                    "inline": False,
                }
            )

            def build_content(user_name: str) -> str:
                return (
                    f"Chào **{user_name}**!\n"
                    f"Ca trực nhật phòng Lab của **{event.team_name}** vừa được cập nhật thời gian:\n"
                    f"📅 **Ngày trực**: {duty_date_str}\n"
                    f"⏰ **Khung giờ**: {time_str}\n"
                    f"👉 Vui lòng dọn dẹp vệ sinh phòng Lab và nộp ảnh minh chứng theo thời gian mới."
                )

            await self._dispatch_to_users(
                user_ids=target_user_ids,
                title=title,
                content_generator=build_content,
                fields=fields,
            )
            logger.info(
                f"Successfully sent duty updated notifications to {len(target_user_ids)} users for duty_id={event.duty_id}"
            )
        except Exception as e:
            logger.error(f"Error in _send_duty_updated_notification_task: {e}")

    async def _send_submitted_notification_task(self, event: DutySubmitted) -> None:
        """Gửi thông báo nộp minh chứng trực nhật lên Discord room quản lý."""
        try:
            room_id = settings.DISCORD_PERMISSION_ROOM_ID
            user = self.user_repo.get_by_id(event.submitted_by)
            user_name = user.name if user else f"Thành viên #{event.submitted_by}"

            t_ids = (
                event.team_id if isinstance(event.team_id, list) else [event.team_id]
            )
            t_names = [
                getattr(t, "team_name", None)
                or getattr(t, "name", None)
                or f"Nhóm #{tid}"
                for tid in t_ids
                if (t := self.team_repo.get_by_id(tid))
            ]
            team_name = ", ".join(t_names) if t_names else f"Nhóm #{t_ids}"

            fields = [
                {"name": "👥 Nhóm phụ trách", "value": team_name, "inline": True},
                {"name": "📅 Ngày trực", "value": event.duty_date, "inline": True},
                {"name": "👤 Người nộp", "value": user_name, "inline": True},
                {
                    "name": "📸 Số lượng ảnh minh chứng",
                    "value": f"{event.image_count} ảnh",
                    "inline": True,
                },
                {
                    "name": "⏰ Thời gian nộp",
                    "value": event.submitted_at,
                    "inline": True,
                },
                {
                    "name": "⚡ Trạng thái",
                    "value": "Chờ Admin/HR phê duyệt",
                    "inline": True,
                },
            ]

            full_url = f"{settings.FRONTEND_URL}/dashboard/duties"

            payload = NotificationPayload(
                user_id=event.submitted_by,
                title="🧹 [TRỰC NHẬT] MINH CHỨNG CẦN DUYỆT",
                content=(
                    f"**{user_name}** vừa gửi minh chứng trực nhật cho **{team_name}** "
                    f"ngày **{event.duty_date}**.\n"
                    "👉 Vui lòng Admin/HR kiểm tra hình ảnh và xét duyệt trên hệ thống."
                ),
                category=NotificationCategory.DUTY,
                level=NotificationLevel.INFO,
                fields=fields,
                action_url=full_url,
            )

            if room_id:
                delivery_res = await self.dispatcher.dispatch_room(
                    room_id=room_id, payload=payload
                )
                if delivery_res.success:
                    logger.info(
                        f"Sent duty approval notification to Discord room for duty_id={event.duty_id}"
                    )
                else:
                    logger.warning(
                        f"Failed to send duty approval notification to Discord room for duty_id={event.duty_id}"
                    )
            else:
                logger.info(
                    f"Duty submitted for duty_id={event.duty_id} by {user_name} (DISCORD_PERMISSION_ROOM_ID not set)"
                )
        except Exception as e:
            logger.error(f"Error in DutyNotificationHandler task: {e}")
