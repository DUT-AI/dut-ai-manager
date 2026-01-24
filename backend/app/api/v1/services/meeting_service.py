from datetime import date, datetime
from typing import List, Optional

from fastapi import UploadFile

from app.api.v1.repositories.meeting_repository import (
    MeetingParticipantRepository,
    MeetingRepository,
)
from app.api.v1.services.user_service import UserService
from app.api.v1.services.violation_service import ViolationService
from app.core.minio_service import MinioService
from app.core.repository_factory import RepositoryFactory
from app.models.meeting import Meeting, MeetingParticipant, ParticipantStatus
from app.models.permission_request import RequestCategory
from app.schemas.activity import ViolationCreate
from app.schemas.meeting import MeetingCreate, MeetingUpdate
from app.schemas.response import BadRequestException
from app.utils.datetime import get_current_utc7_time


class MeetingService:
    def __init__(
        self,
        repo_factory: RepositoryFactory,
        meeting_repo: MeetingRepository,
        participant_repo: MeetingParticipantRepository,
        user_service: UserService,
        violation_service: ViolationService,
        minio_service: MinioService,
    ):
        self.repo_factory = repo_factory
        self.meeting_repo = meeting_repo
        self.participant_repo = participant_repo
        self.user_service = user_service
        self.violation_service = violation_service
        self.minio_service = minio_service

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Meeting]:
        return self.meeting_repo.get_all_with_participants(skip, limit)

    def get_by_id(self, meeting_id: int) -> Optional[Meeting]:
        return self.meeting_repo.get_with_participants(meeting_id)

    def get_by_date(self, target_date: date) -> List[Meeting]:
        return self.meeting_repo.get_by_date(target_date)

    def create_meeting(self, data: MeetingCreate) -> Meeting:
        # Create meeting
        meeting = Meeting(
            title=data.title,
            content=data.content,
            start_time=data.start_time,
            end_time=data.end_time,
        )
        new_meeting = self.meeting_repo.create(meeting)

        # Collect user IDs
        user_ids = set()
        if data.user_ids:
            user_ids.update(data.user_ids)

        if data.team_ids:
            team_user_ids = self.repo_factory.team.get_user_ids_by_teams(data.team_ids)
            user_ids.update(team_user_ids)

        # Create participants
        for user_id in user_ids:
            participant = MeetingParticipant(
                meeting_id=new_meeting.id,
                user_id=user_id,
                status=ParticipantStatus.NOT_JOINED,
            )
            self.participant_repo.create(participant)

        return self.get_by_id(new_meeting.id)

    def update_meeting(self, meeting_id: int, data: MeetingUpdate) -> Meeting:
        meeting = self.meeting_repo.get_by_id(meeting_id)
        if not meeting:
            raise BadRequestException("Meeting not found")

        # Update meeting fields
        if data.title is not None:
            meeting.title = data.title
        if data.content is not None:
            meeting.content = data.content
        if data.start_time is not None:
            meeting.start_time = data.start_time
        if data.end_time is not None:
            meeting.end_time = data.end_time

        self.meeting_repo.update(meeting)

        # Update participants if team_ids or user_ids are provided
        # The requirement says if adjusting members, replacement should happen.
        # We check if either team_ids or user_ids is provided (even if empty list)
        if data.team_ids is not None or data.user_ids is not None:
            # Delete existing participants
            existing_participants = self.participant_repo.get_by_meeting(meeting_id)
            for p in existing_participants:
                self.participant_repo.delete(p)

            # Collect new user IDs
            user_ids = set()
            if data.user_ids:
                user_ids.update(data.user_ids)

            if data.team_ids:
                team_user_ids = self.repo_factory.team.get_user_ids_by_teams(
                    data.team_ids
                )
                user_ids.update(team_user_ids)

            # Create new participants
            for user_id in user_ids:
                participant = MeetingParticipant(
                    meeting_id=meeting_id,
                    user_id=user_id,
                    status=ParticipantStatus.NOT_JOINED,
                )
                self.participant_repo.create(participant)

        return self.get_by_id(meeting_id)

    def delete_meeting(self, meeting_id: int) -> bool:
        meeting = self.meeting_repo.get_by_id(meeting_id)
        if not meeting:
            raise BadRequestException("Meeting not found")

        # Delete participants first (although cascade should handle it if set up in DB,
        # but let's be explicit if not sure about DB level foreign key constraint)
        # Actually, SQLModel relationship with cascade="all, delete-orphan" usually handles it in memory,
        # but for DB delete we might need to be careful.

        participants = self.participant_repo.get_by_meeting(meeting_id)
        for p in participants:
            self.participant_repo.delete(p)

        return self.meeting_repo.delete(meeting)

    async def check_in(
        self, meeting_id: int, user_id: int, image: UploadFile
    ) -> MeetingParticipant:
        participant = self.participant_repo.get_by_meeting_and_user(meeting_id, user_id)
        if not participant:
            raise BadRequestException("User is not a participant of this meeting")

        if participant.status == ParticipantStatus.JOINED:
            raise BadRequestException("User already checked in")

        meeting = participant.meeting
        now = get_current_utc7_time()

        # Upload image to MinIO
        file_content = await image.read()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        filename = f"meetings/{meeting_id}/{user_id}_{timestamp}_{image.filename}"

        image_url = self.minio_service.upload_file(
            file_data=file_content,
            filename=filename,
            content_type=image.content_type or "image/jpeg",
        )

        # Lateness logic
        if now > meeting.start_time:
            # Check for permission request
            meeting_date = meeting.start_time.date()
            permissions = self.repo_factory.permission_request.get_by_date(meeting_date)
            # Filter for this user and 'đi trễ sinh hoạt' category
            user_permission = next(
                (
                    p
                    for p in permissions
                    if p.created_by == user_id and p.category == RequestCategory.LATE
                ),
                None,
            )

            check_in_time_str = now.strftime("%H:%M:%S")
            if not user_permission:
                # No permission
                violation_reason = f"Đi trễ không phép buổi sinh hoạt: {meeting.title} (Thời gian check in: {check_in_time_str})"
                await self.violation_service.create(
                    ViolationCreate(user_id=user_id, reason=violation_reason, date=now),
                    is_system=True,
                )
            else:
                # Has permission, check if still late beyond permission end_time
                # Convert permission end_time to datetime for comparison
                perm_end_time = datetime.combine(meeting_date, user_permission.end_time)
                if now > perm_end_time:
                    perm_end_time_str = user_permission.end_time.strftime("%H:%M:%S")
                    violation_reason = f"Đi trễ có phép buổi sinh hoạt: {meeting.title} (Thời gian xin phép: {perm_end_time_str} Thời gian check in: {check_in_time_str})"
                    await self.violation_service.create(
                        ViolationCreate(
                            user_id=user_id, reason=violation_reason, date=now
                        ),
                        is_system=True,
                    )

        # Update participant
        participant.check_in_at = now
        participant.status = ParticipantStatus.JOINED
        participant.link_image = image_url

        return self.participant_repo.update(participant)
