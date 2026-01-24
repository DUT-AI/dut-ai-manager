from typing import List

from fastapi import APIRouter, File, UploadFile, status

from app.core.deps import CurrentUser, ServiceFactoryDI
from app.schemas.meeting import (
    MeetingCreate,
    MeetingResponse,
    MeetingUpdate,
    ParticipantResponse,
)
from app.schemas.response import ApiResponse

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.post(
    "", response_model=ApiResponse[MeetingResponse], status_code=status.HTTP_201_CREATED
)
async def create_meeting(
    data: MeetingCreate,
    service_factory: ServiceFactoryDI,
    _current_user: CurrentUser,
):
    """Create a new meeting (Admin/Leader only usually, but current requirement doesn't specify permissions)"""
    meeting = service_factory.meeting.create_meeting(data)
    return ApiResponse.success(data=meeting, message="Meeting created successfully")


@router.get("", response_model=ApiResponse[List[MeetingResponse]])
async def get_meetings(
    service_factory: ServiceFactoryDI,
    _current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
):
    """Get all meetings"""
    meetings = service_factory.meeting.get_all(skip, limit)
    return ApiResponse.success(data=meetings, message="Meetings retrieved successfully")


@router.get("/{meeting_id}", response_model=ApiResponse[MeetingResponse])
async def get_meeting(
    meeting_id: int,
    service_factory: ServiceFactoryDI,
    _current_user: CurrentUser,
):
    """Get meeting by ID"""
    meeting = service_factory.meeting.get_by_id(meeting_id)
    if not meeting:
        return ApiResponse.not_found(message="Meeting not found")
    return ApiResponse.success(data=meeting, message="Meeting retrieved successfully")


@router.post("/check-in", response_model=ApiResponse[ParticipantResponse])
async def check_in(
    meeting_id: int,
    user_id: int,
    service_factory: ServiceFactoryDI,
    _current_user: CurrentUser,
    image: UploadFile = File(...),
):
    """Check in to a meeting with an image"""
    participant = await service_factory.meeting.check_in(meeting_id, user_id, image)
    return ApiResponse.success(data=participant, message="Check-in successful")


@router.put("/{meeting_id}", response_model=ApiResponse[MeetingResponse])
async def update_meeting(
    meeting_id: int,
    data: MeetingUpdate,
    service_factory: ServiceFactoryDI,
    _current_user: CurrentUser,
):
    """Update meeting and optionally replace participants"""
    meeting = service_factory.meeting.update_meeting(meeting_id, data)
    return ApiResponse.success(data=meeting, message="Meeting updated successfully")


@router.delete("/{meeting_id}", response_model=ApiResponse[bool])
async def delete_meeting(
    meeting_id: int,
    service_factory: ServiceFactoryDI,
    _current_user: CurrentUser,
):
    """Delete meeting and its participants"""
    success = service_factory.meeting.delete_meeting(meeting_id)
    return ApiResponse.success(data=success, message="Meeting deleted successfully")
