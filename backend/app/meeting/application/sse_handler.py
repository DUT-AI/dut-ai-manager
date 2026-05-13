from app.meeting.domain.events import ParticipantCheckedIn, ParticipantCheckedOut
from app.shared.infrastructure.sse import sse_broadcaster


class MeetingSseHandler:
    """
    Lắng nghe các sự kiện của Meeting và đẩy vào SseBroadcaster.
    """

    async def handle(self, event: ParticipantCheckedIn | ParticipantCheckedOut):
        # Xác định loại event
        event_type = (
            "CHECK_IN" if isinstance(event, ParticipantCheckedIn) else "CHECK_OUT"
        )

        # Chuẩn bị dữ liệu gửi đi
        message = {
            "type": event_type,
            "meeting_id": event.meeting_id,
            "user_id": event.user_id,
            "meeting_title": event.meeting_title,
            "timestamp": (
                event.check_in_at.isoformat()
                if isinstance(event, ParticipantCheckedIn)
                else event.check_out_at.isoformat()
            ),
        }

        logger.info(f"📣 Broadcasting SSE event: {event_type} for user {event.user_id}")
        # Phát tin qua SSE
        await sse_broadcaster.broadcast(message)
