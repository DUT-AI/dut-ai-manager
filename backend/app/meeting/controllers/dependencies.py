from dishka.integrations.fastapi import FromDishka, inject
from fastapi import HTTPException, status

from app.core.deps import CurrentUser
from app.core.permissions import MeetingPermission
from app.meeting.application import GetMeetingsUseCase
from app.shared.application.response import BadRequestException


@inject
async def check_meeting_ownership(
    meeting_id: int,
    current_user: CurrentUser,
    uc: FromDishka[GetMeetingsUseCase],
):
    """Kiểm tra quyền sở hữu cuộc họp (Admin, Leader, hoặc Creator)."""
    is_admin = any(
        r.lower() in ["admin", "superadmin", "leader", "manager"]
        for r in (current_user.role_names or [])
    )
    if is_admin:
        return

    meeting = uc.get_by_id(meeting_id)
    if not meeting:
        raise BadRequestException(
            "Không tìm thấy buổi học", status_code=status.HTTP_404_NOT_FOUND
        )

    if meeting.created_by != current_user.id:
        raise BadRequestException(
            message="Bạn không có quyền chỉnh sửa hoặc xóa buổi họp này",
            status_code=status.HTTP_403_FORBIDDEN,
        )


@inject
async def check_meeting_evaluation_permission(
    meeting_id: int,
    current_user: CurrentUser,
    uc: FromDishka[GetMeetingsUseCase],
):
    """Kiểm tra quyền đánh giá cuộc họp (Admin, Creator, hoặc Trainer)."""
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    is_admin = any(
        r.lower() in ["admin", "superadmin", "leader", "manager"]
        for r in (current_user.role_names or [])
    ) or (
        MeetingPermission.CREATE in (current_user.permissions or set())
        or MeetingPermission.UPDATE in (current_user.permissions or set())
    )

    if is_admin:
        return

    meeting = uc.get_by_id(meeting_id)
    if not meeting:
        raise BadRequestException(
            "Không tìm thấy buổi học", status_code=status.HTTP_404_NOT_FOUND
        )

    is_creator = (
        meeting.created_by is not None and meeting.created_by == current_user.id
    )
    is_trainer = meeting.creator is not None and meeting.creator.id == current_user.id

    if not (is_creator or is_trainer):
        raise BadRequestException(
            message="Bạn không có quyền đánh giá buổi học này",
            status_code=status.HTTP_403_FORBIDDEN,
        )
