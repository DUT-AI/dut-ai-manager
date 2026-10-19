from datetime import date
from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, Header, Query, status

from app.billing.application.use_cases import (
    CreateInvoiceUseCase,
    CreateMonthlyInvoicesUseCase,
    DeleteInvoiceUseCase,
    GetInvoicesUseCase,
    HandleSePayWebhookUseCase,
    UpdateInvoiceStatusUseCase,
    UpdateInvoiceUseCase,
)
from app.billing.domain.entity import InvoiceStatus
from app.billing.schemas import (
    BillingSummaryResponse,
    InvoiceCreate,
    InvoiceResponse,
    InvoiceStatusUpdate,
    InvoiceUpdate,
    MonthlyInvoiceCreate,
    MonthlyInvoicePreviewResponse,
    SePayWebhookPayload,
)
from app.core.deps import CurrentUser, PermissionChecker
from app.core.permissions import BillingPermission
from app.shared.application.pagination import PaginationParams
from app.shared.application.response import ApiResponse, PaginationMeta

router = APIRouter(prefix="/billing", tags=["Billing"])


@router.post(
    "/",
    response_model=ApiResponse[list[InvoiceResponse]],
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_invoice(
    data: InvoiceCreate,
    create_uc: FromDishka[CreateInvoiceUseCase],
    _: Annotated[CurrentUser, Depends(PermissionChecker(BillingPermission.CREATE))],
):
    """
    Admin creates an invoice for one or multiple users.
    """
    invoices = await create_uc.execute(
        user_id=data.user_id,
        user_ids=data.user_ids,
        team_id=data.team_id,
        items_data=[item.model_dump() for item in data.items],
        billing_period=data.billing_period,
        description=data.description,
    )
    return ApiResponse.created(
        data=[InvoiceResponse.from_domain(inv) for inv in invoices]
    )


@router.put(
    "/{invoice_id}",
    response_model=ApiResponse[InvoiceResponse],
)
@inject
async def update_invoice(
    invoice_id: int,
    data: InvoiceUpdate,
    update_uc: FromDishka[UpdateInvoiceUseCase],
    _: Annotated[CurrentUser, Depends(PermissionChecker(BillingPermission.UPDATE))],
):
    """
    Admin edits an invoice.
    """
    invoice = update_uc.execute(
        invoice_id=invoice_id,
        items_data=[item.model_dump() for item in data.items],
        description=data.description,
        new_status=data.status,
    )
    return ApiResponse.success(data=InvoiceResponse.from_domain(invoice))


@router.patch(
    "/{invoice_id}/status",
    response_model=ApiResponse[InvoiceResponse],
)
@inject
async def update_invoice_status(
    invoice_id: int,
    data: InvoiceStatusUpdate,
    update_status_uc: FromDishka[UpdateInvoiceStatusUseCase],
    _: Annotated[CurrentUser, Depends(PermissionChecker(BillingPermission.UPDATE))],
):
    """
    Admin updates invoice payment status (e.g. PAID, PENDING, CANCELLED).
    """
    invoice = await update_status_uc.execute(
        invoice_id=invoice_id,
        new_status=data.status,
    )
    return ApiResponse.success(data=InvoiceResponse.from_domain(invoice))


@router.post(
    "/monthly",
    response_model=ApiResponse[MonthlyInvoicePreviewResponse | list[InvoiceResponse]],
)
@inject
async def create_monthly_invoices(
    data: MonthlyInvoiceCreate,
    monthly_uc: FromDishka[CreateMonthlyInvoicesUseCase],
    _: Annotated[CurrentUser, Depends(PermissionChecker(BillingPermission.CREATE))],
):
    """
    Admin creates monthly invoices in bulk.
    Can be used for Preview (execute=False) or Execution (execute=True).
    """
    result = await monthly_uc.execute(
        month=data.month,
        year=data.year,
        team_id=data.team_id,
        user_ids=data.user_ids,
        violation_price=data.violation_price,
        fund_amount=data.fund_amount,
        extra_items=[item.model_dump() for item in data.extra_items],
        execute=data.execute,
    )

    if not data.execute:
        return ApiResponse.success(data=MonthlyInvoicePreviewResponse(**result))

    # If executed, return list of created invoices
    invoices = [InvoiceResponse.from_domain(inv) for inv in result["invoices"]]
    return ApiResponse.created(data=invoices)


@router.get("/me", response_model=ApiResponse[list[InvoiceResponse]])
@inject
async def get_my_invoices(
    get_uc: FromDishka[GetInvoicesUseCase],
    current_user: CurrentUser,
):
    """
    Get invoices for the current logged-in user.
    """
    assert current_user.id is not None
    invoices = get_uc.get_user_invoices(current_user.id)
    data = [InvoiceResponse.from_domain(inv) for inv in invoices]
    return ApiResponse.success(data=data)


@router.get("/", response_model=ApiResponse[list[InvoiceResponse]])
@inject
async def get_all_invoices(
    get_uc: FromDishka[GetInvoicesUseCase],
    _: Annotated[CurrentUser, Depends(PermissionChecker(BillingPermission.READ))],
    pagination: Annotated[PaginationParams, Depends()],
    user_id: int | None = Query(default=None),
    team_id: int | None = Query(default=None),
    bill_status: InvoiceStatus | None = Query(default=None),
    billing_period: date | None = Query(default=None),
):
    """
    Get all invoices with server-side pagination (Admin only).
    """
    invoices, total = get_uc.get_paged_invoices(
        user_id=user_id,
        status=bill_status,
        billing_period=billing_period,
        team_id=team_id,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    meta = PaginationMeta.create(
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )
    data = [InvoiceResponse.from_domain(inv) for inv in invoices]
    return ApiResponse.success(data=data, pagination=meta)


@router.get("/report/matrix", response_model=ApiResponse[list[InvoiceResponse]])
@inject
async def get_matrix_report(
    get_uc: FromDishka[GetInvoicesUseCase],
    _: Annotated[CurrentUser, Depends(PermissionChecker(BillingPermission.READ))],
    start_month: int = Query(...),
    start_year: int = Query(...),
    end_month: int = Query(...),
    end_year: int = Query(...),
    user_ids: list[int] = Query(default=[]),
):
    """
    Get invoices for the matrix report (Admin only).
    """
    invoices = get_uc.get_matrix_report(
        start_month=start_month,
        start_year=start_year,
        end_month=end_month,
        end_year=end_year,
        user_ids=user_ids if user_ids else None,
    )

    data = [InvoiceResponse.from_domain(inv) for inv in invoices]
    return ApiResponse.success(data=data)


@router.get("/summary", response_model=ApiResponse[BillingSummaryResponse])
@inject
async def get_billing_summary(
    get_uc: FromDishka[GetInvoicesUseCase],
    _: Annotated[CurrentUser, Depends(PermissionChecker(BillingPermission.READ))],
    user_id: int | None = Query(default=None),
    team_id: int | None = Query(default=None),
    billing_period: date | None = Query(default=None),
):
    """
    Get billing summary statistics (total, paid, unpaid) across all invoices.
    Admin only.
    """
    summary = get_uc.get_summary(
        billing_period=billing_period,
        team_id=team_id,
        user_id=user_id,
    )
    return ApiResponse.success(data=BillingSummaryResponse(**summary))


@router.get("/{invoice_id}", response_model=ApiResponse[InvoiceResponse])
@inject
async def get_invoice_details(
    invoice_id: int,
    get_uc: FromDishka[GetInvoicesUseCase],
    _: Annotated[CurrentUser, Depends(PermissionChecker(BillingPermission.READ))],
):
    """
    Get detailed information for a specific invoice.
    """
    invoice = get_uc.get_invoice_details(invoice_id)

    return ApiResponse.success(data=InvoiceResponse.from_domain(invoice))


@router.post("/webhook/sepay")
@inject
async def sepay_webhook(
    payload: SePayWebhookPayload,
    handle_uc: FromDishka[HandleSePayWebhookUseCase],
    authorization: Annotated[str | None, Header()] = None,
):
    """
    SePay Webhook endpoint.
    Handles payment notifications from SePay.
    """
    # Extract token from Authorization header (SePay sends 'Apikey <token>')
    auth_token = None
    if authorization and authorization.startswith("Apikey "):
        auth_token = authorization.split(" ")[1]

    success = await handle_uc.execute(payload.model_dump(), auth_token=auth_token)

    if success:
        return {"success": True}
    return {"success": False, "message": "Transaction not matched or already processed"}


@router.delete("/{invoice_id}", response_model=ApiResponse[bool])
@inject
async def delete_invoice(
    invoice_id: int,
    delete_uc: FromDishka[DeleteInvoiceUseCase],
    _: Annotated[CurrentUser, Depends(PermissionChecker(BillingPermission.DELETE))],
):
    """
    Admin deletes an invoice.
    Only possible if invoice is NOT PAID.
    """
    success = delete_uc.execute(invoice_id)
    return ApiResponse.success(data=success)
