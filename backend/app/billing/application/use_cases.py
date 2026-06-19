import calendar
import random
import string
from datetime import date, datetime

from fastapi import status

from app.billing.domain.entity import (
    Invoice,
    InvoiceItem,
    InvoiceItemType,
    InvoiceStatus,
)
from app.billing.infrastructure.repository import InvoiceRepository
from app.core.config import settings
from app.shared.application.response import BadRequestException
from app.team.infrastructure.repository import TeamRepository
from app.violation.infrastructure.repository import ViolationRepository


class CreateInvoiceUseCase:
    """UseCase for Admin to create an invoice for a user."""

    def __init__(self, repo: InvoiceRepository):
        self.repo = repo

    def execute(
        self,
        user_id: int,
        items_data: list[dict],
        billing_period: date,
        description: str | None = None,
    ) -> Invoice:
        # 1. Calculate total amount and create items
        total_amount = 0
        invoice_items = []

        for item in items_data:
            item_type = InvoiceItemType(item["item_type"])
            amount = item.get("amount", 0)

            # Rule: Violation price is fixed at 20,000 VND
            if item_type == InvoiceItemType.VIOLATION:
                amount = 20000

            total_amount += amount
            invoice_items.append(
                InvoiceItem(
                    item_type=item_type,
                    reference_id=item.get("reference_id"),
                    amount=amount,
                    note=item.get("note", ""),
                )
            )

        if total_amount <= 0:
            raise BadRequestException("Tổng số tiền hóa đơn phải lớn hơn 0")

        # 2. Generate unique reference code
        # Format: DUT[RANDOM_6_CHARS]
        reference_code = self._generate_reference_code()

        # 3. Create Invoice entity
        invoice = Invoice(
            user_id=user_id,
            amount=total_amount,
            status=InvoiceStatus.PENDING,
            description=description or f"Thanh toán các khoản thu - {reference_code}",
            reference_code=reference_code,
            billing_period=billing_period,
            items=invoice_items,
        )

        # 4. Save
        return self.repo.save_invoice(invoice)

    def _generate_reference_code(self, length: int = 6) -> str:
        """Gần mã tham chiếu duy nhất cho nội dung chuyển khoản."""
        chars = string.ascii_uppercase + string.digits
        random_str = "".join(random.choice(chars) for _ in range(length))
        return f"DUT{random_str}"


class UpdateInvoiceUseCase:
    """UseCase to edit an unpaid invoice."""

    def __init__(self, repo: InvoiceRepository):
        self.repo = repo

    def execute(
        self, invoice_id: int, items_data: list[dict], description: str | None = None
    ) -> Invoice:
        # 1. Get the invoice
        invoice = self.repo.get_by_id(invoice_id)
        if not invoice:
            raise BadRequestException(
                "Hóa đơn không tồn tại", status_code=status.HTTP_404_NOT_FOUND
            )

        if invoice.status == InvoiceStatus.PAID:
            raise BadRequestException("Không thể sửa hóa đơn đã thanh toán")

        # 2. Calculate new amount and create items
        total_amount = 0
        new_items = []

        for item in items_data:
            item_type = InvoiceItemType(item["item_type"])
            amount = item.get("amount", 0)

            if item_type == InvoiceItemType.VIOLATION:
                amount = 20000

            total_amount += amount
            new_items.append(
                InvoiceItem(
                    item_type=item_type,
                    reference_id=item.get("reference_id"),
                    amount=amount,
                    note=item.get("note", ""),
                )
            )

        if total_amount <= 0:
            raise BadRequestException("Tổng số tiền hóa đơn phải lớn hơn 0")

        # 3. Update fields
        invoice.amount = total_amount
        invoice.items = new_items
        if description is not None:
            invoice.description = description

        # 4. Save
        return self.repo.save_invoice(invoice)


class HandleSePayWebhookUseCase:
    """UseCase to handle incoming SePay Webhook notifications."""

    def __init__(self, repo: InvoiceRepository):
        self.repo = repo

    def execute(self, webhook_data: dict, auth_token: str | None = None) -> bool:
        # 1. Verify token if configured
        if (
            settings.SEPAY_WEBHOOK_SECRET
            and auth_token != settings.SEPAY_WEBHOOK_SECRET
        ):
            raise BadRequestException(
                "Lỗi xác thực Webhook", status_code=status.HTTP_401_UNAUTHORIZED
            )

        # 2. Extract reference code from transaction content
        content = webhook_data.get("content", "")
        transfer_amount = webhook_data.get("transferAmount", 0)
        transaction_id = str(webhook_data.get("id", ""))

        # Find invoice by matching reference_code in content
        invoice = self._find_invoice_by_content(content)

        if not invoice:
            return False

        if invoice.status == InvoiceStatus.PAID:
            return True

        # 3. Validate amount
        if transfer_amount < invoice.amount:
            return False

        # 4. Update Invoice status
        invoice.status = InvoiceStatus.PAID
        invoice.transaction_id = transaction_id

        self.repo.save_invoice(invoice)

        return True

    def _find_invoice_by_content(self, content: str) -> Invoice | None:
        """Tìm hóa đơn bằng cách quét mã tham chiếu trong nội dung chuyển khoản."""
        import re

        match = re.search(r"DUT[A-Z0-9]{6}", content.upper())
        if match:
            ref_code = match.group(0)
            return self.repo.get_by_reference_code(ref_code)
        return None


class GetInvoicesUseCase:
    """UseCase to retrieve invoices."""

    def __init__(self, repo: InvoiceRepository):
        self.repo = repo

    def get_user_invoices(self, user_id: int) -> list[Invoice]:
        return self.repo.get_by_user_id(user_id)

    def get_invoice_details(self, invoice_id: int) -> Invoice:
        invoice = self.repo.get_by_id(invoice_id)
        if not invoice:
            raise BadRequestException(
                "Invoice not found", status_code=status.HTTP_404_NOT_FOUND
            )
        return invoice

    def get_all_invoices(
        self,
        user_id: int | None = None,
        status: str | None = None,
        billing_period: date | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Invoice]:
        return self.repo.get_all_active(
            user_id=user_id,
            status=status,
            billing_period=billing_period,
            skip=skip,
            limit=limit,
        )

    def get_matrix_report(
        self,
        start_month: int,
        start_year: int,
        end_month: int,
        end_year: int,
        user_ids: list[int] | None = None,
    ) -> list[Invoice]:
        try:
            start_date = date(year=start_year, month=start_month, day=1)
            end_date = date(year=end_year, month=end_month, day=1)
        except ValueError:
            raise BadRequestException(
                "Invalid date range", status_code=status.HTTP_400_BAD_REQUEST
            )

        return self.repo.get_matrix_report(start_date, end_date, user_ids)


class QRGenerator:
    """Utility to generate VietQR URL for an invoice."""

    @staticmethod
    def get_url(invoice: Invoice) -> str:
        """Builds the SePay VietQR image URL."""
        base_url = "https://qr.sepay.vn/img"
        params = {
            "bank": settings.SEPAY_BANK_CODE,
            "acc": settings.SEPAY_ACCOUNT_NO,
            "amount": invoice.amount,
            "des": invoice.reference_code,
        }
        query_str = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{base_url}?{query_str}"


class CreateMonthlyInvoicesUseCase:
    """UseCase to create invoices in bulk for a month."""

    def __init__(
        self,
        invoice_repo: InvoiceRepository,
        violation_repo: ViolationRepository,
        team_repo: TeamRepository,
    ):
        self.invoice_repo = invoice_repo
        self.violation_repo = violation_repo
        self.team_repo = team_repo

    def execute(
        self,
        month: int,
        year: int,
        team_id: int | None = None,
        user_ids: list[int] = [],
        violation_price: int = 20000,
        fund_amount: int = 50000,
        extra_items: list[dict] = [],
        execute: bool = False,
    ) -> dict:
        target_users = {}  # user_id -> user_name
        for uid in user_ids:
            target_users[uid] = f"User #{uid}"

        if team_id:
            team = self.team_repo.get_by_id_with_members(team_id)
            if team:
                for member in team.members:
                    target_users[member.user_id] = member.user_name

        if not target_users:
            raise BadRequestException("Không tìm thấy người dùng nào để tạo hóa đơn")

        preview_items = []
        created_invoices = []

        # 2. Process each user
        for uid, uname in target_users.items():
            # Get violations
            violations = self.violation_repo.get_by_month(
                month=month, year=year, user_id=uid
            )
            violation_count = len(violations)
            violation_total = violation_count * violation_price

            user_name = uname

            total_amount = violation_total + fund_amount
            for item in extra_items:
                total_amount += item.get("amount", 0)

            if total_amount <= 0:
                continue

            description = f"Hóa đơn tháng {month:02d}/{year}"

            preview_items.append(
                {
                    "user_id": uid,
                    "user_name": user_name,
                    "violation_count": violation_count,
                    "violation_amount": violation_total,
                    "fund_amount": fund_amount,
                    "total_amount": total_amount,
                    "description": description,
                }
            )

            if execute:
                # Build items
                invoice_items = []
                if violation_count > 0:
                    invoice_items.append(
                        InvoiceItem(
                            item_type=InvoiceItemType.VIOLATION,
                            amount=violation_total,
                            note=f"Vi phạm tháng {month:02d}/{year} ({violation_count} lỗi)",
                        )
                    )
                if fund_amount > 0:
                    invoice_items.append(
                        InvoiceItem(
                            item_type=InvoiceItemType.FUND,
                            amount=fund_amount,
                            note=f"Tiền quỹ tháng {month:02d}/{year}",
                        )
                    )
                for ei in extra_items:
                    invoice_items.append(
                        InvoiceItem(
                            item_type=InvoiceItemType(ei["item_type"]),
                            amount=ei["amount"],
                            note=ei.get("note", ""),
                        )
                    )

                # Generate reference
                ref = self._generate_reference_code()

                invoice = Invoice(
                    user_id=uid,
                    amount=total_amount,
                    status=InvoiceStatus.PENDING,
                    description=description,
                    reference_code=ref,
                    billing_period=date(year, month, 1),
                    items=invoice_items,
                )

                saved = self.invoice_repo.save_invoice(invoice)
                created_invoices.append(saved)

        return {
            "month": month,
            "year": year,
            "items": preview_items,
            "invoices": created_invoices if execute else [],
        }

    def _generate_reference_code(self, length: int = 6) -> str:
        import random
        import string

        chars = string.ascii_uppercase + string.digits
        return f"DUT{''.join(random.choice(chars) for _ in range(length))}"


class DeleteInvoiceUseCase:
    """UseCase for Admin to delete an invoice."""

    def __init__(self, repo: InvoiceRepository):
        self.repo = repo

    def execute(self, invoice_id: int) -> bool:
        # 1. Get invoice
        invoice = self.repo.get_by_id(invoice_id)
        if not invoice:
            raise BadRequestException(
                "Không tìm thấy hóa đơn", status_code=status.HTTP_404_NOT_FOUND
            )

        # 2. Safety check: Do not allow deleting PAID invoices
        if invoice.status == InvoiceStatus.PAID:
            raise BadRequestException("Không thể xóa hóa đơn đã được thanh toán")

        # 3. Delete (soft delete by default in repository)
        return self.repo.delete_by_id(invoice_id)
