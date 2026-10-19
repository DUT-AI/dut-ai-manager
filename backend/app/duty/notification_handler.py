import asyncio
from datetime import datetime
from loguru import logger

from app.core.config import settings
from app.duty.domain.events import DutyScheduled, DutySubmitted, DutyUpdated
from app.duty.infrastructure.repository import DutyRepository
from app.meeting.domain.events import MeetingUpdated
from app.meeting.domain.value_objects import ParticipantStatus
from app.meeting.infrastructure.repository import MeetingRepository
from app.shared.application.event_handler import EventHandler
from app.shared.infrastructure.notification_payload import (
    NotificationCategory,
    NotificationLevel,
    NotificationPayload,
)
from app.shared.infrastructure.notification_service import NotificationService
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
        notification_service: NotificationService,
        user_repo: UserRepository,
        team_repo: TeamRepository,
        meeting_repo: MeetingRepository | None = None,
        duty_repo: DutyRepository | None = None,
    ):
        self.notification_service = notification_service
        self.user_repo = user_repo
        self.team_repo = team_repo
        self.meeting_repo = meeting_repo
        self.duty_repo = duty_repo

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

    async def _send_scheduled_notification_task(self, event: DutyScheduled) -> None:
        """
        Gửi thông báo phân công ca trực nhật tới:
        - Các học viên có mặt trong buổi meeting hôm đó (cả học viên lớp chính thức và học viên lớp khác đổi ca qua).
        - Nếu là ca trực tự do, gửi tới tất cả học viên thuộc các nhóm phụ trách.
        """
        try:
            duty = self.duty_repo.get_by_id(event.duty_id) if self.duty_repo else None
            meeting_id = event.meeting_id or (duty.meeting_id if duty else None)
            meeting = self.meeting_repo.get_by_id(meeting_id) if (meeting_id and self.meeting_repo) else None

            # 1. Thu thập danh sách user_id cần gửi thông báo
            candidate_user_ids: list[int] = []

            if meeting and meeting.participants:
                meeting_creator_id = getattr(meeting, "created_by", None)
                for p in meeting.participants:
                    if getattr(p, "is_deleted", False):
                        continue
                    if meeting_creator_id and p.user_id == meeting_creator_id:
                        continue
                    if p.status == ParticipantStatus.ABSENT_EXCUSED:
                        continue
                    candidate_user_ids.append(p.user_id)

            # Nếu ca tự do hoặc meeting chưa có participants, lấy theo thành viên các nhóm trực
            if not candidate_user_ids:
                t_ids = event.team_id if isinstance(event.team_id, list) else [event.team_id]
                for t_id in t_ids:
                    team = self.team_repo.get_by_id(t_id)
                    if team and team.member_ids:
                        candidate_user_ids.extend(team.member_ids)
                    elif team and team.members:
                        candidate_user_ids.extend(m.user_id for m in team.members if m.user_id)

            target_user_ids = list(dict.fromkeys(candidate_user_ids))
            if not target_user_ids:
                logger.warning(
                    f"No participants or team members found to notify for duty_id={event.duty_id}"
                )
                return

            try:
                if isinstance(event.duty_date, str):
                    dt_obj = datetime.strptime(event.duty_date, "%Y-%m-%d").date()
                else:
                    dt_obj = event.duty_date
                duty_date_str = dt_obj.strftime("%d/%m/%Y")
            except Exception:
                duty_date_str = str(event.duty_date)

            time_str = "Theo lịch sinh hoạt phòng Lab"
            if duty and duty.start_time and duty.end_time:
                time_str = f"{duty.start_time.strftime('%H:%M')} – {duty.end_time.strftime('%H:%M')}"
            elif duty and duty.start_time:
                time_str = f"Từ {duty.start_time.strftime('%H:%M')}"
            elif meeting and meeting.start_time and meeting.end_time:
                time_str = f"{meeting.start_time.strftime('%H:%M')} – {meeting.end_time.strftime('%H:%M')}"

            title = "🧹 [TRỰC NHẬT] PHÂN CÔNG TRỰC NHẬT PHÒNG LAB"
            fields = [
                {"name": "👥 Nhóm phụ trách", "value": event.team_name, "inline": True},
                {"name": "📅 Ngày trực", "value": duty_date_str, "inline": True},
                {"name": "⏰ Khung giờ trực", "value": time_str, "inline": True},
            ]
            if duty and duty.note:
                fields.append({"name": "📝 Ghi chú phân công", "value": duty.note, "inline": False})

            fields.append({
                "name": "📌 Lưu ý quan trọng",
                "value": "Vui lòng quét dọn, lau bàn ghế, sàn phòng Lab và nộp ảnh minh chứng thành phẩm trước 22:00 cùng ngày để tránh bị phạt vi phạm.",
                "inline": False,
            })

            for uid in target_user_ids:
                user = self.user_repo.get_by_id(uid)
                user_name = user.name if user else f"Thành viên #{uid}"

                payload = NotificationPayload(
                    user_id=uid,
                    title=title,
                    content=(
                        f"Chào **{user_name}**!\n"
                        f"Bạn có lịch phân công trực nhật phòng Lab cho **{event.team_name}** "
                        f"vào ngày **{duty_date_str}** ({time_str}).\n"
                        f"👉 Vui lòng dọn dẹp vệ sinh phòng Lab và nộp ảnh minh chứng lên hệ thống."
                    ),
                    category=NotificationCategory.DUTY,
                    level=NotificationLevel.INFO,
                    image_asset="meme-lam-viec.webp",
                    fields=fields,
                    action_url=f"{settings.FRONTEND_HOST}/dashboard/duties",
                )
                await self.notification_service.send_to_user(payload)

            logger.info(
                f"Successfully sent duty schedule notifications to {len(target_user_ids)} users for duty_id={event.duty_id}"
            )
        except Exception as e:
            logger.error(f"Error in _send_scheduled_notification_task: {e}")

    async def _send_meeting_rescheduled_notification_task(
        self, event: MeetingUpdated
    ) -> None:
        """
        Xử lý khi lịch meeting thay đổi (ngày/giờ):
        - Tự động đồng bộ ca trực nhật liên kết với meeting đó (nếu đã tạo ca trực trong DB).
        - Gửi thông báo trực nhật điều chỉnh đến các học viên liên quan.
        """
        try:
            start_dt = datetime.fromisoformat(event.start_time)
            end_dt = datetime.fromisoformat(event.end_time)
            new_date = start_dt.date()
            new_start_time = start_dt.time()
            new_end_time = end_dt.time()
            duty_date_str = new_date.strftime("%d/%m/%Y")
            time_str = f"{new_start_time.strftime('%H:%M')} – {new_end_time.strftime('%H:%M')}"

            # 1. Tự động đồng bộ các ca trực gắn với meeting trong DB
            linked_duties = (
                self.duty_repo.get_by_meeting_id(event.meeting_id)
                if self.duty_repo
                else []
            )
            for d in linked_duties:
                d.duty_date = new_date
                d.start_time = new_start_time
                d.end_time = new_end_time
                self.duty_repo.save(d)

            # 2. Thu thập danh sách các nhóm Gen 2
            teams = self.team_repo.get_all_with_members()
            gen2_teams = [
                t
                for t in teams
                if t.id
                and (
                    "gen 2" in (t.team_name or "").lower()
                    or "gen2" in (t.team_name or "").lower()
                )
            ]
            team_users = {
                t.id: {m.user_id for m in t.members if m.user_id}
                for t in teams
                if t.id
            }
            all_gen2_user_ids = set()
            for gt in gen2_teams:
                all_gen2_user_ids.update(team_users.get(gt.id, set()))

            # 3. Thu thập danh sách học viên cần thông báo
            meeting = (
                self.meeting_repo.get_by_id(event.meeting_id)
                if self.meeting_repo
                else None
            )
            candidate_user_ids: list[int] = []

            if meeting and meeting.participants:
                meeting_creator_id = getattr(meeting, "created_by", None)
                for p in meeting.participants:
                    if getattr(p, "is_deleted", False):
                        continue
                    if meeting_creator_id and p.user_id == meeting_creator_id:
                        continue
                    if p.status == ParticipantStatus.ABSENT_EXCUSED:
                        continue
                    candidate_user_ids.append(p.user_id)
            elif event.user_ids:
                candidate_user_ids.extend(event.user_ids)

            p_ids = set(candidate_user_ids)
            title_lower = (event.title or "").lower()
            is_gen2_title = ("gen 2" in title_lower) or ("gen2" in title_lower)
            has_gen2_participants = bool(p_ids & all_gen2_user_ids)

            # Nếu là meeting thuần Gen 1 (không có ai thuộc Gen 2 và tiêu đề không phải Gen 2) -> không gửi thông báo trực nhật
            if p_ids and not has_gen2_participants and not is_gen2_title:
                logger.info(
                    f"Meeting {event.meeting_id} is pure Gen 1, skipping duty reschedule notification"
                )
                return

            # Xác định tên nhóm phụ trách
            team_name = "Nhóm Gen 2"
            if linked_duties and linked_duties[0].team_name:
                team_name = linked_duties[0].team_name
            elif linked_duties and linked_duties[0].team_id:
                t_ids = (
                    linked_duties[0].team_id
                    if isinstance(linked_duties[0].team_id, list)
                    else [linked_duties[0].team_id]
                )
                t_names = [
                    self.team_repo.get_by_id(t).team_name
                    for t in t_ids
                    if self.team_repo.get_by_id(t)
                ]
                team_name = ", ".join(t_names) if t_names else f"Nhóm #{t_ids}"
            else:
                best_team = None
                best_overlap = 0
                for t in gen2_teams:
                    overlap = len(p_ids & team_users.get(t.id, set()))
                    if overlap > best_overlap:
                        best_overlap = overlap
                        best_team = t
                if not best_team:
                    day_idx = new_date.weekday()
                    for t in gen2_teams:
                        tn = (t.team_name or "").lower()
                        if day_idx == 1 and ("thứ 3" in tn or "thu 3" in tn):
                            best_team = t
                            break
                        elif day_idx == 2 and ("thứ 4" in tn or "thu 4" in tn):
                            best_team = t
                            break
                        elif day_idx == 3 and ("thứ 5" in tn or "thu 5" in tn):
                            best_team = t
                            break
                        elif day_idx == 5 and ("thứ 7" in tn or "thu 7" in tn):
                            best_team = t
                            break
                if not best_team and gen2_teams:
                    best_team = gen2_teams[0]
                team_name = best_team.team_name if best_team else "Nhóm Gen 2"

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

            for uid in target_user_ids:
                user = self.user_repo.get_by_id(uid)
                user_name = user.name if user else f"Thành viên #{uid}"

                payload = NotificationPayload(
                    user_id=uid,
                    title=title,
                    content=(
                        f"Chào **{user_name}**!\n"
                        f"Buổi sinh hoạt **'{event.title}'** đã thay đổi thời gian, "
                        f"lịch trực nhật phòng Lab của **{team_name}** được điều chỉnh tương ứng sang:\n"
                        f"📅 **Ngày trực mới**: {duty_date_str}\n"
                        f"⏰ **Khung giờ mới**: {time_str}\n"
                        f"👉 Vui lòng lưu ý khung giờ mới để trực nhật và nộp ảnh minh chứng đúng hạn."
                    ),
                    category=NotificationCategory.DUTY,
                    level=NotificationLevel.INFO,
                    image_asset="meme-lam-viec.webp",
                    fields=fields,
                    action_url=f"{settings.FRONTEND_HOST}/dashboard/duties",
                )
                await self.notification_service.send_to_user(payload)

            logger.info(
                f"Successfully sent duty rescheduled notifications to {len(target_user_ids)} users for meeting_id={event.meeting_id}"
            )
        except Exception as e:
            logger.error(f"Error in _send_meeting_rescheduled_notification_task: {e}")

    async def _send_duty_updated_notification_task(
        self, event: DutyUpdated
    ) -> None:
        """
        Xử lý khi ca trực tự do hoặc ca trực được chỉnh sửa (giờ/ngày/nhóm/ghi chú):
        - Gửi thông báo đến học viên phụ trách để cập nhật thời gian trực nhật mới.
        """
        try:
            duty = self.duty_repo.get_by_id(event.duty_id) if self.duty_repo else None
            candidate_user_ids: list[int] = []

            # Nếu có gắn với meeting
            if duty and duty.meeting_id and self.meeting_repo:
                meeting = self.meeting_repo.get_by_id(duty.meeting_id)
                if meeting and meeting.participants:
                    meeting_creator_id = getattr(meeting, "created_by", None)
                    for p in meeting.participants:
                        if getattr(p, "is_deleted", False):
                            continue
                        if meeting_creator_id and p.user_id == meeting_creator_id:
                            continue
                        if p.status == ParticipantStatus.ABSENT_EXCUSED:
                            continue
                        candidate_user_ids.append(p.user_id)

            # Nếu là ca trực tự do hoặc chưa lấy được từ meeting
            if not candidate_user_ids:
                t_ids = (
                    event.team_id
                    if isinstance(event.team_id, list)
                    else [event.team_id]
                )
                for t_id in t_ids:
                    team = self.team_repo.get_by_id(t_id)
                    if team and team.member_ids:
                        candidate_user_ids.extend(team.member_ids)
                    elif team and team.members:
                        candidate_user_ids.extend(
                            m.user_id for m in team.members if m.user_id
                        )

            target_user_ids = list(dict.fromkeys(candidate_user_ids))
            if not target_user_ids:
                logger.warning(
                    f"No users to notify for updated duty_id={event.duty_id}"
                )
                return

            try:
                if isinstance(event.duty_date, str):
                    dt_obj = datetime.strptime(event.duty_date, "%Y-%m-%d").date()
                else:
                    dt_obj = event.duty_date
                duty_date_str = dt_obj.strftime("%d/%m/%Y")
            except Exception:
                duty_date_str = str(event.duty_date)

            time_str = "Theo phân công của Admin/HR"
            if duty and duty.start_time and duty.end_time:
                time_str = f"{duty.start_time.strftime('%H:%M')} – {duty.end_time.strftime('%H:%M')}"
            elif duty and duty.start_time:
                time_str = f"Từ {duty.start_time.strftime('%H:%M')}"

            title = "🧹 [CẬP NHẬT LỊCH TRỰC NHẬT] ĐIỀU CHỈNH THỜI GIAN TRỰC"
            fields = [
                {"name": "👥 Nhóm phụ trách", "value": event.team_name, "inline": True},
                {"name": "📅 Ngày trực mới", "value": duty_date_str, "inline": True},
                {"name": "⏰ Giờ trực mới", "value": time_str, "inline": True},
            ]
            if duty and duty.note:
                fields.append(
                    {"name": "📝 Ghi chú phân công", "value": duty.note, "inline": False}
                )

            fields.append({
                "name": "📌 Lưu ý",
                "value": "Lịch trực nhật đã được cập nhật lại. Vui lòng lưu ý thời gian mới để hoàn thành trực nhật và nộp ảnh minh chứng đúng hạn trước 22:00 cùng ngày.",
                "inline": False,
            })

            for uid in target_user_ids:
                user = self.user_repo.get_by_id(uid)
                user_name = user.name if user else f"Thành viên #{uid}"

                payload = NotificationPayload(
                    user_id=uid,
                    title=title,
                    content=(
                        f"Chào **{user_name}**!\n"
                        f"Ca trực nhật phòng Lab của **{event.team_name}** vừa được cập nhật thời gian:\n"
                        f"📅 **Ngày trực**: {duty_date_str}\n"
                        f"⏰ **Khung giờ**: {time_str}\n"
                        f"👉 Vui lòng dọn dẹp vệ sinh phòng Lab và nộp ảnh minh chứng theo thời gian mới."
                    ),
                    category=NotificationCategory.DUTY,
                    level=NotificationLevel.INFO,
                    image_asset="meme-lam-viec.webp",
                    fields=fields,
                    action_url=f"{settings.FRONTEND_HOST}/dashboard/duties",
                )
                await self.notification_service.send_to_user(payload)

            logger.info(
                f"Successfully sent duty updated notifications to {len(target_user_ids)} users for duty_id={event.duty_id}"
            )
        except Exception as e:
            logger.error(f"Error in _send_duty_updated_notification_task: {e}")

    async def _send_submitted_notification_task(
        self, event: DutySubmitted
    ) -> None:
        try:
            room_id = settings.DISCORD_PERMISSION_ROOM_ID
            user = self.user_repo.get_by_id(event.submitted_by)
            user_name = user.name if user else f"Thành viên #{event.submitted_by}"

            t_ids = (
                event.team_id
                if isinstance(event.team_id, list)
                else [event.team_id]
            )
            t_names = []
            for t_id in t_ids:
                team = self.team_repo.get_by_id(t_id)
                name = (
                    getattr(team, "team_name", None)
                    or getattr(team, "name", None)
                    or f"Nhóm #{t_id}"
                )
                t_names.append(name)
            team_name = ", ".join(t_names)

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
                action_url=f"{settings.FRONTEND_HOST}/dashboard/duties",
            )

            if room_id:
                success = await self.notification_service.send_to_room(
                    room_id=room_id, payload=payload, channel="discord"
                )
                if success:
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
