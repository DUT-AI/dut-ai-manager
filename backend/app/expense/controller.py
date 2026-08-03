"""
Expense Controller — FastAPI router endpoints.
"""

from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, Query, status

from app.core.deps import CurrentUser, PermissionChecker
from app.core.permissions import ExpensePermission
from app.expense.application.use_cases import (
    CreateExpenseUseCase,
    DeleteExpenseUseCase,
    GetExpenseByIdUseCase,
    GetExpenseSummaryUseCase,
    GetExpensesUseCase,
    UpdateExpenseStatusUseCase,
    UpdateExpenseUseCase,
)
from app.expense.domain.entity import ExpenseStatus
from app.expense.schemas import (
    ExpenseInvoiceCreate,
    ExpenseInvoiceResponse,
    ExpenseInvoiceStatusUpdate,
    ExpenseInvoiceUpdate,
    ExpenseSummaryResponse,
)
from app.shared.application.response import ApiResponse

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.get(
    "/summary",
    response_model=ApiResponse[ExpenseSummaryResponse],
)
@inject
async def get_expense_summary(
    summary_uc: FromDishka[GetExpenseSummaryUseCase],
    _: Annotated[CurrentUser, Depends(PermissionChecker(ExpensePermission.READ))],
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None, ge=2000, le=2100),
    spender_id: int | None = Query(None),
    team_id: int | None = Query(None),
):
    """Get expense summary statistics for a given month/year, spender_id, and team_id."""
    res = summary_uc.execute(
        month=month, year=year, spender_id=spender_id, team_id=team_id
    )
    return ApiResponse.success(data=ExpenseSummaryResponse(**res))


@router.get(
    "/",
    response_model=ApiResponse[list[ExpenseInvoiceResponse]],
)
@inject
async def get_expenses(
    get_uc: FromDishka[GetExpensesUseCase],
    _: Annotated[CurrentUser, Depends(PermissionChecker(ExpensePermission.READ))],
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None, ge=2000, le=2100),
    expense_status: ExpenseStatus | None = Query(None, alias="status"),
    spender_id: int | None = Query(None),
    team_id: int | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Get list of expense invoices filtered by month/year, status, spender_id, and team_id."""
    models = get_uc.execute(
        month=month,
        year=year,
        status=expense_status,
        spender_id=spender_id,
        team_id=team_id,
        limit=limit,
        offset=offset,
    )
    data = [ExpenseInvoiceResponse.model_validate(m) for m in models]
    return ApiResponse.success(data=data)


@router.post(
    "/",
    response_model=ApiResponse[ExpenseInvoiceResponse],
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_expense(
    data: ExpenseInvoiceCreate,
    create_uc: FromDishka[CreateExpenseUseCase],
    current_user: Annotated[
        CurrentUser, Depends(PermissionChecker(ExpensePermission.CREATE))
    ],
):
    """Create a new outgoing expense invoice."""
    model = create_uc.execute(
        expense_date=data.expense_date,
        amount=data.amount,
        description=data.description,
        spender_id=data.spender_id,
        team_id=data.team_id,
        status=data.status,
        payment_date=data.payment_date,
        note=data.note,
        created_by=current_user.id,
    )
    return ApiResponse.created(data=ExpenseInvoiceResponse.model_validate(model))


@router.get(
    "/{expense_id}",
    response_model=ApiResponse[ExpenseInvoiceResponse],
)
@inject
async def get_expense_by_id(
    expense_id: str,
    get_by_id_uc: FromDishka[GetExpenseByIdUseCase],
    _: Annotated[CurrentUser, Depends(PermissionChecker(ExpensePermission.READ))],
):
    """Get detail of an expense invoice by UUID."""
    model = get_by_id_uc.execute(expense_id=expense_id)
    return ApiResponse.success(data=ExpenseInvoiceResponse.model_validate(model))


@router.put(
    "/{expense_id}",
    response_model=ApiResponse[ExpenseInvoiceResponse],
)
@inject
async def update_expense(
    expense_id: str,
    data: ExpenseInvoiceUpdate,
    update_uc: FromDishka[UpdateExpenseUseCase],
    current_user: Annotated[
        CurrentUser, Depends(PermissionChecker(ExpensePermission.UPDATE))
    ],
):
    """Update an expense invoice."""
    model = update_uc.execute(
        expense_id=expense_id,
        expense_date=data.expense_date,
        amount=data.amount,
        description=data.description,
        spender_id=data.spender_id,
        team_id=data.team_id,
        status=data.status,
        payment_date=data.payment_date,
        note=data.note,
        updated_by=current_user.id,
    )
    return ApiResponse.success(data=ExpenseInvoiceResponse.model_validate(model))


@router.patch(
    "/{expense_id}/status",
    response_model=ApiResponse[ExpenseInvoiceResponse],
)
@inject
async def update_expense_status(
    expense_id: str,
    data: ExpenseInvoiceStatusUpdate,
    update_status_uc: FromDishka[UpdateExpenseStatusUseCase],
    current_user: Annotated[
        CurrentUser, Depends(PermissionChecker(ExpensePermission.UPDATE))
    ],
):
    """Update expense status (UNPAID / PAID)."""
    model = update_status_uc.execute(
        expense_id=expense_id,
        status=data.status,
        payment_date=data.payment_date,
        updated_by=current_user.id,
    )
    return ApiResponse.success(data=ExpenseInvoiceResponse.model_validate(model))


@router.delete(
    "/{expense_id}",
    response_model=ApiResponse[bool],
)
@inject
async def delete_expense(
    expense_id: str,
    delete_uc: FromDishka[DeleteExpenseUseCase],
    _: Annotated[CurrentUser, Depends(PermissionChecker(ExpensePermission.DELETE))],
):
    """Delete an expense invoice (soft delete)."""
    result = delete_uc.execute(expense_id=expense_id)
    return ApiResponse.success(data=result)
