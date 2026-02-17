from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import UploadFile, status

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

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        month: Optional[int] = None,
        year: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Meeting]:
        return self.meeting_repo.get_all_with_participants(
            skip, limit, month, year, start_date, end_date
        )

    def get_by_id(self, meeting_id: int) -> Optional[Meeting]:
        meeting = self.meeting_repo.get_with_participants(meeting_id)
        if not meeting:
            raise BadRequestException(
                "Meeting not found", status_code=status.HTTP_404_NOT_FOUND
            )
        return meeting

    def get_by_date(self, target_date: date) -> List[Meeting]:
        return self.meeting_repo.get_by_date(target_date)

    def create_meeting(self, data: MeetingCreate) -> Meeting:
        # Validate seat availability

        # Calculate participants count for new meeting
        user_ids = set()
        if data.user_ids:
            user_ids.update(data.user_ids)

        if data.team_ids:
            team_user_ids = self.repo_factory.team.get_user_ids_by_teams(data.team_ids)
            user_ids.update(team_user_ids)

        current_meeting_participants_count = len(user_ids)

        # Check overlapped meetings
        concurrent_participants = self.meeting_repo.get_concurrent_participants_count(
            data.start_time, data.end_time
        )

        from app.core.config import settings

        total_seats_needed = (
            concurrent_participants + current_meeting_participants_count
        )
        remaining_seats = settings.MAX_SEATS - concurrent_participants

        if total_seats_needed > settings.MAX_SEATS:
            # Ensure remaining seats is not negative in message
            display_remaining = max(0, remaining_seats)
            raise BadRequestException(
                f"Chỗ ngồi không đủ, chỉ còn {display_remaining} chỗ ngồi"
            )

        # Create meeting
        meeting = Meeting(
            title=data.title,
            content=data.content,
            start_time=data.start_time,
            end_time=data.end_time,
            require_check_in=data.require_check_in,
        )
        new_meeting = self.meeting_repo.create(meeting)

        # Create participants (reuse user_ids from validation)
        # We already resolved user_ids and team_ids above into `user_ids` set.
        # But wait, original code did:
        # 75:         user_ids = set()
        # 76:         if data.user_ids:
        # 77:             user_ids.update(data.user_ids)
        # 78:
        # 79:         if data.team_ids:
        # 80:             team_user_ids = self.repo_factory.team.get_user_ids_by_teams(data.team_ids)
        # 81:             user_ids.update(team_user_ids)

        # We can just remove the redundant resolution block below.

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

        # Validate seat availability
        # Calculate new participants count
        new_user_ids = set()
        if data.user_ids:
            new_user_ids.update(data.user_ids)
        if data.team_ids:
            new_user_ids.update(
                self.repo_factory.team.get_user_ids_by_teams(data.team_ids)
            )

        # If updating, we need to know the participant count difference or total
        # The logic here replaces participants, so new_user_ids count is the new count for THIS meeting.

        # However, for update, data.user_ids/team_ids might be None (partial update).
        # We need to handle that. If not provided, use existing participants count?
        # But wait, existing logic deletes and recreates if either is provided.
        # If both are None, participant set doesn't change.

        if data.team_ids is not None or data.user_ids is not None:
            # Logic to calculate new count is complex because we need to check overlap with OTHER meetings.
            # So effectively:
            # 1. Calculate count for THIS meeting (resolving new set).
            # 2. Query DB for sum of participants of ALL OTHER overlapping meetings.
            # 3. Sum (1) + (2) <= MAX_SEATS.
            pass

        # Actually proper implementation requires resolving the final list of user_ids for the meeting
        # THEN checking total concurrently.

        current_meeting_participants_count = 0
        if data.team_ids is not None or data.user_ids is not None:
            user_ids = set()
            if data.user_ids:
                user_ids.update(data.user_ids)
            if data.team_ids:
                user_ids.update(
                    self.repo_factory.team.get_user_ids_by_teams(data.team_ids)
                )
            current_meeting_participants_count = len(user_ids)
        else:
            # Use existing count if not changing participants
            current_meeting_participants_count = len(meeting.participants)

        # Check for overlap with NEW time (or existing time if not changed)
        check_start_time = data.start_time if data.start_time else meeting.start_time
        check_end_time = data.end_time if data.end_time else meeting.end_time

        concurrent_participants = self.meeting_repo.get_concurrent_participants_count(
            check_start_time, check_end_time, exclude_meeting_id=meeting_id
        )

        from app.core.config import settings

        total_seats_needed = (
            concurrent_participants + current_meeting_participants_count
        )
        remaining_seats = settings.MAX_SEATS - concurrent_participants

        if total_seats_needed > settings.MAX_SEATS:
            # Ensure remaining seats is not negative in message
            display_remaining = max(0, remaining_seats)
            raise BadRequestException(
                f"Chỗ ngồi không đủ, chỉ còn {display_remaining} chỗ ngồi"
            )

        # Update meeting fields
        if data.title is not None:
            meeting.title = data.title
        if data.content is not None:
            meeting.content = data.content
        if data.start_time is not None:
            meeting.start_time = data.start_time
        if data.end_time is not None:
            meeting.end_time = data.end_time
        if data.require_check_in is not None:
            meeting.require_check_in = data.require_check_in

        self.meeting_repo.update(meeting)

        # Update participants if team_ids or user_ids are provided
        if data.team_ids is not None or data.user_ids is not None:
            # Delete existing participants
            existing_participants = self.participant_repo.get_by_meeting(meeting_id)
            for p in existing_participants:
                self.participant_repo.delete(p)

            # Since we resolved user_ids for validation above, use it if available, else re-resolve?
            # We resolved it into `user_ids` variable in the if block above.
            # But variable scope in python is function-level, so `user_ids` set should be available.
            # Let's be safe and re-use logic or variable carefully.

            # Re-collect logic to be safe and clean or reuse
            # reusing `user_ids` set from above validation block

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
        self, meeting_id: int, user_ids: List[int], image: UploadFile
    ) -> tuple[List[MeetingParticipant], str]:
        # Upload image to MinIO once
        now = get_current_utc7_time()
        file_content = await image.read()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        # Use first user_id for filename prefix or just generic
        filename = f"meetings/{meeting_id}/checkin_{timestamp}_{image.filename}"

        image_url = self.minio_service.upload_file(
            file_data=file_content,
            filename=filename,
            content_type=image.content_type or "image/jpeg",
        )

        success_names = []
        error_messages = []
        updated_participants = []

        for user_id in user_ids:
            participant = self.participant_repo.get_by_meeting_and_user(
                meeting_id, user_id
            )
            if not participant:
                error_messages.append(
                    f"Người dùng {user_id} không có trong danh sách tham dự"
                )
                continue

            if participant.status == ParticipantStatus.JOINED:
                error_messages.append(f"Người dùng {user_id} đã checkin rồi")
                updated_participants.append(participant)
                continue

            meeting = participant.meeting

            # Lateness logic - only check if meeting requires check-in
            if meeting.require_check_in and now > meeting.start_time:
                # Check for permission request
                meeting_date = meeting.start_time.date()
                permissions = self.repo_factory.permission_request.get_by_date(
                    meeting_date
                )
                # Filter for this user and 'đi trễ sinh hoạt' category
                user_permission = next(
                    (
                        p
                        for p in permissions
                        if p.created_by == user_id
                        and p.category == RequestCategory.LATE
                    ),
                    None,
                )

                check_in_time_str = now.strftime("%H:%M:%S")
                if not user_permission:
                    # No permission
                    violation_reason = f"Đi trễ không phép buổi sinh hoạt: {meeting.title} (Thời gian check in: {check_in_time_str})"
                    await self.violation_service.create(
                        ViolationCreate(
                            user_ids=[user_id], reason=violation_reason, date=now
                        ),
                        is_system=True,
                    )
                else:
                    # Has permission, check if still late beyond permission end_time
                    # Convert permission end_time to datetime for comparison
                    perm_end_time = datetime.combine(
                        meeting_date, user_permission.end_time
                    )
                    if now > perm_end_time:
                        perm_end_time_str = user_permission.end_time.strftime(
                            "%H:%M:%S"
                        )
                        violation_reason = f"Đi trễ có phép buổi sinh hoạt: {meeting.title} (Thời gian xin phép: {perm_end_time_str} Thời gian check in: {check_in_time_str})"
                        await self.violation_service.create(
                            ViolationCreate(
                                user_ids=[user_id], reason=violation_reason, date=now
                            ),
                            is_system=True,
                        )

            # Update participant
            participant.check_in_at = now
            participant.status = ParticipantStatus.JOINED
            participant.link_image = image_url
            updated_p = self.participant_repo.update(participant)
            updated_participants.append(updated_p)

            # Get user name for message
            user_name = participant.user.name if participant.user else str(user_id)
            success_names.append(user_name)

        # Construct message
        message_parts = []
        if success_names:
            message_parts.append(f"Đã ghi nhận {', '.join(success_names)}")

        if error_messages:
            message_parts.append(". ".join(error_messages))

        full_message = ". ".join(message_parts)
        if not full_message:
            full_message = "Không có người dùng nào được checkin"

        return updated_participants, full_message

    def get_participating_meetings(
        self, user_id: int, month: int, year: int
    ) -> List[Meeting]:
        """Get meetings that the user is participating in for a specific month."""
        all_meetings_in_month = self.get_all(limit=1000, month=month, year=year)
        user_meetings = []
        for meeting in all_meetings_in_month:
            # Check if user is in participants
            is_participant = any(p.user_id == user_id for p in meeting.participants)
            if is_participant:
                user_meetings.append(meeting)
        return user_meetings
