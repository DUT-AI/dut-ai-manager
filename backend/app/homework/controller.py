from datetime import datetime
from typing import Annotated, Any

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from app.core.deps import CurrentUser, hasPermission
from app.core.permissions import HomeworkPermission, HomeworkSubmissionPermission
from app.homework.application.dtos import (
    HomeworkCreate,
    HomeworkReportResponse,
    HomeworkResponse,
    HomeworkUpdate,
    HomeworkSubmissionStatusResponse,
)
from app.homework.application.use_cases import HomeworkUseCases
from app.homework.domain.value_objects import HomeworkStatus
from app.shared.application.response import ApiResponse

router = APIRouter(prefix="/homeworks", tags=["homeworks"])


@router.get(
    "",
    response_model=ApiResponse[list[HomeworkResponse]],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
@inject
async def get_all_homeworks(
    use_cases: FromDishka[HomeworkUseCases],
    skip: int = 0,
    limit: int = 100,
    deleted: bool = False,
):
    result = use_cases.get_all(skip=skip, limit=limit, deleted=deleted)
    return ApiResponse.success(data=result)


@router.get(
    "/me",
    response_model=ApiResponse[list[HomeworkResponse]],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
@inject
async def get_my_homeworks(
    current_user: CurrentUser,
    use_cases: FromDishka[HomeworkUseCases],
    skip: int = 0,
    limit: int = 100,
):
    """Get homeworks assigned to the current user"""
    assert current_user.id is not None
    result = use_cases.get_assigned_to_user(current_user.id, skip=skip, limit=limit)
    return ApiResponse.success(data=result)


def parse_int_list(values: Any) -> list[int] | None:
    if values is None:
        return None
    if isinstance(values, str):
        val_str = values.strip()
        if not val_str:
            return []
        if val_str.startswith("[") and val_str.endswith("]"):
            import json
            try:
                parsed = json.loads(val_str)
                return [int(x) for x in parsed if str(x).isdigit()]
            except Exception:
                pass
        return [int(x.strip()) for x in val_str.split(",") if x.strip().isdigit()]
    if isinstance(values, list):
        res = []
        for item in values:
            if isinstance(item, int):
                res.append(item)
            elif isinstance(item, str):
                parsed = parse_int_list(item)
                if parsed:
                    res.extend(parsed)
        return res
    return None


@router.post(
    "",
    response_model=ApiResponse[HomeworkResponse],
    dependencies=[hasPermission(HomeworkPermission.CREATE)],
)
@inject
async def create_homework(
    use_cases: FromDishka[HomeworkUseCases],
    title: str = Form(...),
    deadline: str = Form(...),
    link: str | None = Form(None),
    slug: str | None = Form(None),
    assignee_ids: list[int] | None = Form(None),
    team_ids: list[int] | None = Form(None),
):
    try:
        deadline_dt = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
        if deadline_dt.timestamp() < datetime.now().timestamp():
            raise HTTPException(status_code=400, detail="Hạn nộp không được ở trong quá khứ")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid deadline format")

    parsed_assignees = parse_int_list(assignee_ids)
    parsed_teams = parse_int_list(team_ids)

    data = HomeworkCreate(
        title=title,
        deadline=deadline_dt,
        link=link,
        slug=slug,
        assignee_ids=parsed_assignees,
        team_ids=parsed_teams,
    )

    result = await use_cases.create(data)
    return ApiResponse.success(data=result)



@router.get(
    "/report/unsubmitted",
    response_model=ApiResponse[list[HomeworkReportResponse]],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
@inject
async def get_unsubmitted_report(
    use_cases: FromDishka[HomeworkUseCases],
):
    """Báo cáo bài tập chưa nộp của tất cả active user"""
    print(">>> [API] GET /homeworks/report/unsubmitted CALLED!")
    result = await use_cases.get_unsubmitted_report()
    print(f">>> [API] Returning {len(result)} items. Top item: {result[0].model_dump() if result else None}")
    return ApiResponse.success(data=result)


@router.get(
    "/report/unsubmitted/{user_id}",
    response_model=ApiResponse[list[HomeworkResponse]],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
@inject
async def get_unsubmitted_by_user(
    user_id: int,
    use_cases: FromDishka[HomeworkUseCases],
):
    """Lấy danh sách bài tập chưa nộp của một user cụ thể"""
    result = await use_cases.get_unsubmitted_by_user(user_id)
    return ApiResponse.success(data=result)


@router.get(
    "/{homework_id}/submission-status",
    response_model=ApiResponse[HomeworkSubmissionStatusResponse],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
@inject
async def get_homework_submission_status(
    homework_id: int,
    use_cases: FromDishka[HomeworkUseCases],
):
    """Lấy danh sách người đã nộp / chưa nộp của một bài tập cụ thể"""
    result = await use_cases.get_submission_status(homework_id)
    if not result:
        raise HTTPException(status_code=404, detail="Homework not found")
    return ApiResponse.success(data=result)


@router.get(
    "/{homework_id}",
    response_model=ApiResponse[HomeworkResponse],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
@inject
async def get_homework(
    homework_id: int,
    use_cases: FromDishka[HomeworkUseCases],
):
    result = use_cases.get_by_id(homework_id)
    if not result:
        raise HTTPException(status_code=404, detail="Homework not found")
    return ApiResponse.success(data=result)



@router.put(
    "/{homework_id}",
    response_model=ApiResponse[HomeworkResponse],
    dependencies=[hasPermission(HomeworkPermission.UPDATE)],
)
@inject
async def update_homework(
    homework_id: int,
    use_cases: FromDishka[HomeworkUseCases],
    title: str | None = Form(None),
    deadline: str | None = Form(None),
    link: str | None = Form(None),
    slug: str | None = Form(None),
    assignee_ids: list[int] | None = Form(None),
    team_ids: list[int] | None = Form(None),
):
    deadline_dt = None
    if deadline:
        try:
            deadline_dt = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
            if deadline_dt.timestamp() < datetime.now().timestamp():
                raise HTTPException(status_code=400, detail="Hạn nộp không được ở trong quá khứ")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid deadline format")

    data = HomeworkUpdate(
        title=title,
        deadline=deadline_dt,
        link=link,
        slug=slug,
        assignee_ids=parse_int_list(assignee_ids),
        team_ids=parse_int_list(team_ids),
    )

    result = await use_cases.update(homework_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Homework not found")
    return ApiResponse.success(data=result)



@router.delete(
    "/{homework_id}",
    response_model=ApiResponse[bool],
    dependencies=[hasPermission(HomeworkPermission.DELETE)],
)
@inject
async def delete_homework(
    homework_id: int,
    use_cases: FromDishka[HomeworkUseCases],
):
    result = use_cases.delete(homework_id)
    if not result:
        raise HTTPException(status_code=404, detail="Homework not found")
    return ApiResponse.success(data=result)


@router.put("/{homework_id}/restore", response_model=ApiResponse[HomeworkResponse])
@inject
async def restore_homework(
    homework_id: int,
    use_cases: FromDishka[HomeworkUseCases],
    _current_user: Annotated[CurrentUser, hasPermission(HomeworkPermission.DELETE)],
):
    result = use_cases.restore(homework_id)
    if not result:
        raise HTTPException(status_code=404, detail="Homework not found or not deleted")
    return ApiResponse.success(data=result)



