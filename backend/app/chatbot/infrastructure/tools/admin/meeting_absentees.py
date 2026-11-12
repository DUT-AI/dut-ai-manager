"""Admin tool to list absent participants of the most recent meeting."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.chatbot.infrastructure.tools.base import BaseChatbotTool
from app.core.permissions import MeetingPermission
from app.core.principal import AuthPrincipal
from app.meeting.domain.value_objects import ParticipantStatus
from app.meeting.infrastructure.model import Meeting, MeetingParticipant
from app.user.infrastructure.model import UserModel


class AdminGetMeetingAbsenteesTool(BaseChatbotTool):
    name = "admin_get_meeting_absentees"
    description = (
        "DÀNH CHO BAN TỔ CHỨC CUỘC HỌP: Liệt kê danh sách chi tiết (họ tên, email, vai trò) "
        "của các thành viên vắng mặt không phép trong buổi họp gần nhất hoặc theo tên buổi họp."
    )
    parameters = {
        "type": "object",
        "properties": {
            "meeting_title": {
                "type": "string",
                "description": "Tên buổi họp cần tra cứu (để trống sẽ tra cứu buổi họp mới nhất).",
            }
        },
        "required": [],
    }
    required_permissions = [MeetingPermission.READ.value]

    def execute(
        self, session: Session, args: dict[str, Any], user: AuthPrincipal
    ) -> dict[str, Any]:
        stmt = (
            select(Meeting)
            .order_by(Meeting.start_time.desc())
        )
        meeting_title = args.get("meeting_title")
        if meeting_title:
            stmt = stmt.where(Meeting.title.ilike(f"%{meeting_title}%"))

        meeting = session.scalars(stmt).first()
        if not meeting:
            return {"message": "Không tìm thấy cuộc họp phù hợp."}

        p_stmt = (
            select(MeetingParticipant, UserModel)
            .join(UserModel, UserModel.id == MeetingParticipant.user_id)
            .where(
                MeetingParticipant.meeting_id == meeting.id,
                MeetingParticipant.status.in_([
                    ParticipantStatus.ABSENT_UNEXCUSED.value,
                    ParticipantStatus.NOT_JOINED.value,
                ]),
            )
            .order_by(UserModel.name.asc())
        )
        results = session.execute(p_stmt).all()

        absentees = [
            {
                "user_id": u.id,
                "name": u.name,
                "email": u.email,
                "role": p.role,
                "status": p.status.value if hasattr(p.status, "value") else str(p.status),
            }
            for p, u in results
        ]

        return {
            "meeting_id": meeting.id,
            "meeting_title": meeting.title,
            "meeting_date": meeting.start_time.strftime("%d/%m/%Y %H:%M") if meeting.start_time else None,
            "absentee_count": len(absentees),
            "absentees": absentees,
        }

