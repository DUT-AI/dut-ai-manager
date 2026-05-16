from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, Header, status

from app.billing.application.use_cases import (
    CreateInvoiceUseCase,
    CreateMonthlyInvoicesUseCase,
    DeleteInvoiceUseCase,
    GetInvoicesUseCase,
    HandleSePayWebhookUseCase,
    UpdateInvoiceUseCase,
)
from app.billing.schemas import (
    InvoiceCreate,
    InvoiceResponse,
    InvoiceUpdate,
    MonthlyInvoiceCreate,
    MonthlyInvoicePreviewResponse,
    SePayWebhookPayload,
)
from app.core.deps import CurrentUser, PermissionChecker
from app.core.permissions import BillingPermission
from app.shared.application.response import ApiResponse

router = APIRouter(prefix="/billing", tags=["Billing"])


@router.post(
    "/",
    response_model=ApiResponse[InvoiceResponse],
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_invoice(
    data: InvoiceCreate,
    create_uc: FromDishka[CreateInvoiceUseCase],
    _: Annotated[CurrentUser, Depends(PermissionChecker(BillingPermission.CREATE))],
):
    """
    Admin creates an invoice for a user.
    """
    invoice = create_uc.execute(
        user_id=data.user_id,
        items_data=[item.model_dump() for item in data.items],
        description=data.description,
    )
    return ApiResponse.created(data=InvoiceResponse.from_domain(invoice))


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
    Admin edits an unpaid invoice.
    """
    invoice = update_uc.execute(
        invoice_id=invoice_id,
        items_data=[item.model_dump() for item in data.items],
        description=data.description,
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
    result = monthly_uc.execute(
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
    skip: int = 0,
    limit: int = 100,
):
    """
    Get all invoices (Admin only).
    """
    invoices = get_uc.get_all_invoices(skip=skip, limit=limit)
    data = [InvoiceResponse.from_domain(inv) for inv in invoices]
    return ApiResponse.success(data=data)


from fastapi import Query


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

    success = handle_uc.execute(payload.model_dump(), auth_token=auth_token)

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
