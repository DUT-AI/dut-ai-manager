from app.capacity.application.service import CapacityService
from app.capacity.domain.entity import CapacityMonitor
from app.core.deps import CurrentUser
from app.shared.application.response import ApiResponse
from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter

router = APIRouter(prefix="/capacity", tags=["Capacity"])


@router.get("/status", response_model=ApiResponse[CapacityMonitor])
@inject
async def get_capacity_status(
    service: FromDishka[CapacityService],
    _current_user: CurrentUser,
):
    """Lấy trạng thái capacity hiện tại"""
    monitor = service.get_current_status()
    return ApiResponse.success(data=monitor)


@router.get("/forecast")
@inject
async def get_capacity_forecast(
    service: FromDishka[CapacityService],
    _current_user: CurrentUser,
):
    """Lấy dự báo 30 phút tới"""
    monitor = service.calculate_current()
    return ApiResponse.success(data={
        "current": monitor.current_count,
        "incoming": monitor.incoming_count,
        "outgoing": monitor.outgoing_count,
        "future": monitor.future_count,
        "status": monitor.status.value,
        "max_capacity": monitor.MAX_CAPACITY,
    })
