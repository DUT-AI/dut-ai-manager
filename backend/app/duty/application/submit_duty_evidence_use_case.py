"""
Submit Duty Evidence Use Case.
"""

from datetime import datetime, time, timezone
from typing import cast
from zoneinfo import ZoneInfo

from fastapi import HTTPException, UploadFile, status

from app.duty.application.dtos import DutyResponse
from app.duty.domain.entity import DutyStatus
from app.duty.domain.events import DutySubmitted
from app.duty.infrastructure.repository import DutyRepository
from app.meeting.domain.value_objects import ParticipantStatus
from app.meeting.infrastructure.repository import MeetingRepository
from app.shared.domain.event_bus import DomainEvent, EventBus
from app.shared.infrastructure.minio_service import MinioService
from app.team.infrastructure.repository import TeamRepository


class SubmitDutyEvidenceUseCase:
    """Nộp ảnh thành phẩm, checklist và ghi chú trực nhật."""

    def __init__(
        self,
        duty_repo: DutyRepository,
        team_repo: TeamRepository,
        minio_service: MinioService,
        meeting_repo: MeetingRepository | None = None,
        event_bus: type[EventBus] = EventBus,
    ):
        self.duty_repo = duty_repo
        self.team_repo = team_repo
        self.minio_service = minio_service
        self.meeting_repo = meeting_repo
        self.event_bus = event_bus

    async def execute(
        self,
        duty_id: int,
        user_id: int,
        files: list[UploadFile],
        checklist: list[dict] | None = None,
        note: str | None = None,
        is_admin: bool = False,
    ) -> DutyResponse:
        duty = self.duty_repo.get_by_id(duty_id)
        if not duty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ca trực nhật không tồn tại",
            )

        now = datetime.now(timezone.utc)

        # Kiểm tra deadline: 22:00 cùng ngày (Admin/HR có quyền nộp thử hoặc nộp thay)
        deadline_dt = datetime.combine(
            duty.duty_date, time(22, 0, 0), tzinfo=ZoneInfo("Asia/Ho_Chi_Minh")
        ).astimezone(timezone.utc)
        if not is_admin and now > deadline_dt and duty.status != DutyStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Đã quá hạn nộp minh chứng trực nhật (Hạn chót: 22:00 ngày {duty.duty_date.strftime('%d/%m/%Y')})",
            )

        # Kiểm tra quyền nộp (nếu không phải admin / HR)
        if not is_admin:
            t_ids = duty.team_id if isinstance(duty.team_id, list) else [duty.team_id]
            is_authorized = False

            # 1. Thành viên chính thức của nhóm trực nhật
            for t_id in t_ids:
                team = self.team_repo.get_by_id(t_id)
                if team and user_id in team.member_ids:
                    is_authorized = True
                    break

            # 2. Hoặc học viên tham gia buổi sinh hoạt hôm đó (bao gồm cả bạn đổi ca sang)
            if not is_authorized and duty.meeting_id and self.meeting_repo:
                meeting = self.meeting_repo.get_by_id(duty.meeting_id)
                if meeting and meeting.participants:
                    is_authorized = any(
                        p.user_id == user_id
                        and not getattr(p, "is_deleted", False)
                        and p.status
                        not in (
                            ParticipantStatus.ABSENT_EXCUSED,
                            ParticipantStatus.ABSENT_UNEXCUSED,
                        )
                        for p in meeting.participants
                    )

            if not is_authorized:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bạn không thuộc nhóm trực nhật hoặc buổi sinh hoạt phụ trách ca này",
                )

        # Kiểm tra ít nhất 1 việc và ít nhất 1 ảnh (nếu ca chưa có ảnh)
        existing_urls = list(duty.evidence_image_urls or [])
        if not files and not existing_urls:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vui lòng tải lên ít nhất 1 ảnh minh chứng thành phẩm",
            )

        target_checklist = checklist if checklist is not None else duty.checklist
        has_task = any(
            bool(item.get("checked") or item.get("completed"))
            for item in (target_checklist or [])
        )

        if not has_task:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vui lòng tích chọn ít nhất 1 đầu việc trực nhật đã thực hiện",
            )

        # Upload files lên MinIO
        uploaded_urls: list[str] = []
        for file in files:
            if not file.filename:
                continue
            content = await file.read()
            ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
            ts_str = now.strftime("%Y%m%d_%H%M%S_%f")
            object_name = f"duties/{duty_id}/{ts_str}.{ext}"

            url = await self.minio_service.upload_file(
                file_data=content,
                filename=object_name,
                content_type=file.content_type or "image/jpeg",
            )
            uploaded_urls.append(url)

        all_urls = existing_urls + uploaded_urls

        duty.submit_evidence(
            submitted_by=user_id,
            image_urls=all_urls,
            checklist=target_checklist,
            note=note or duty.note,
            submitted_at=now,
        )

        saved = self.duty_repo.save(duty)
        assert saved.id is not None

        await self.event_bus.publish(
            cast(
                DomainEvent,
                DutySubmitted(
                    duty_id=saved.id,
                    team_id=saved.team_id,
                    duty_date=str(saved.duty_date),
                    submitted_by=user_id,
                    image_count=len(saved.evidence_image_urls),
                    submitted_at=now.isoformat(),
                ),
            )
        )

        return DutyResponse.model_validate(saved)
