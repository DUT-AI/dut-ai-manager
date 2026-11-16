import random
import re
import string
import unicodedata
import urllib.parse
from datetime import UTC, date, datetime

from fastapi import status

from app.billing.domain.entity import (
    Invoice,
    InvoiceItem,
    InvoiceItemType,
    InvoiceStatus,
)
from app.billing.domain.events import InvoiceCreated, InvoicePaid
from app.billing.infrastructure.repository import InvoiceRepository
from app.core.config import settings
from app.shared.application.response import BadRequestException
from app.shared.domain.event_bus import EventBus
from app.team.infrastructure.repository import TeamRepository
from app.violation.infrastructure.repository import ViolationRepository


class CreateInvoiceUseCase:
    """UseCase for Admin to create an invoice for a user."""

    def __init__(self, repo: InvoiceRepository):
        self.repo = repo

    async def execute(
        self,
        items_data: list[dict],
        billing_period: date,
        team_id: int | None = None,
        fund_code: str = "DUT_AI",
        user_id: int | None = None,
        user_ids: list[int] | None = None,
        description: str | None = None,
    ) -> list[Invoice]:
        # Determine target user IDs
        target_uids = (
            list(user_ids) if user_ids else ([user_id] if user_id is not None else [])
        )
        if not target_uids:
            raise BadRequestException("Vui lòng chọn ít nhất 1 thành viên")

        # 1. Calculate total amount and create template items
        total_amount = 0
        template_items = []

        for item in items_data:
            item_type = InvoiceItemType(item["item_type"])
            amount = item.get("amount", 0)

            # Default violation amount to 20,000 VND if not specified or <= 0
            if item_type == InvoiceItemType.VIOLATION and amount <= 0:
                amount = 20000

            total_amount += amount
            template_items.append(
                {
                    "item_type": item_type,
                    "reference_id": item.get("reference_id"),
                    "amount": amount,
                    "note": item.get("note", ""),
                }
            )

        if total_amount <= 0:
            raise BadRequestException("Tổng số tiền hóa đơn phải lớn hơn 0")

        created_invoices = []
        for uid in target_uids:
            # Generate unique reference code
            reference_code = self._generate_reference_code()

            invoice_items = [
                InvoiceItem(
                    item_type=it["item_type"],
                    reference_id=it["reference_id"],
                    amount=it["amount"],
                    note=it["note"],
                )
                for it in template_items
            ]

            invoice = Invoice(
                user_id=uid,
                fund_code=fund_code,
                team_id=team_id,
                amount=total_amount,
                status=InvoiceStatus.PENDING,
                description=description
                or f"Thanh toán các khoản thu - {reference_code}",
                reference_code=reference_code,
                billing_period=billing_period,
                items=invoice_items,
            )
            saved = self.repo.save_invoice(invoice)
            created_invoices.append(saved)

            # Phát sự kiện InvoiceCreated
            if saved.id:
                await EventBus.publish(
                    InvoiceCreated(
                        invoice_id=saved.id,
                        user_id=saved.user_id,
                        amount=saved.amount,
                        reference_code=saved.reference_code,
                        description=saved.description,
                        billing_period=saved.billing_period,
                    )
                )

        return created_invoices

    def _generate_reference_code(self, length: int = 6) -> str:
        """Gần mã tham chiếu duy nhất cho nội dung chuyển khoản."""
        chars = string.ascii_uppercase + string.digits
        random_str = "".join(random.choice(chars) for _ in range(length))
        return f"DUT{random_str}"


class UpdateInvoiceUseCase:
    """UseCase to edit an invoice."""

    def __init__(self, repo: InvoiceRepository):
        self.repo = repo

    def execute(
        self,
        invoice_id: int,
        items_data: list[dict],
        description: str | None = None,
        new_status: InvoiceStatus | None = None,
        fund_code: str | None = None,
        team_id: int | None = None,
    ) -> Invoice:
        # 1. Get the invoice
        invoice = self.repo.get_by_id(invoice_id)
        if not invoice:
            raise BadRequestException(
                "Hóa đơn không tồn tại", status_code=status.HTTP_404_NOT_FOUND
            )

        # 2. Calculate new amount and create items
        total_amount = 0
        new_items = []

        for item in items_data:
            item_type = InvoiceItemType(item["item_type"])
            amount = item.get("amount", 0)

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
        if fund_code is not None:
            invoice.fund_code = fund_code
        if team_id is not None:
            invoice.team_id = team_id
        if description is not None:
            invoice.description = description
        if new_status is not None:
            invoice.status = new_status
            if new_status == InvoiceStatus.PAID and not invoice.transaction_id:
                invoice.transaction_id = (
                    f"MANUAL_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
                )

        # 4. Save
        return self.repo.save_invoice(invoice)


class UpdateInvoiceStatusUseCase:
    """UseCase to update an invoice's payment status (e.g. manual payment by Admin)."""

    def __init__(self, repo: InvoiceRepository):
        self.repo = repo

    async def execute(self, invoice_id: int, new_status: InvoiceStatus) -> Invoice:
        invoice = self.repo.get_by_id(invoice_id)
        if not invoice:
            raise BadRequestException(
                "Hóa đơn không tồn tại", status_code=status.HTTP_404_NOT_FOUND
            )

        invoice.status = new_status
        if new_status == InvoiceStatus.PAID:
            if not invoice.transaction_id:
                invoice.transaction_id = (
                    f"MANUAL_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
                )

            # Publish event if marked as PAID
            if invoice.id:
                await EventBus.publish(
                    InvoicePaid(
                        invoice_id=invoice.id,
                        user_id=invoice.user_id,
                        amount=invoice.amount,
                        reference_code=invoice.reference_code,
                        transaction_id=invoice.transaction_id,
                        paid_at=datetime.now(UTC),
                    )
                )

        return self.repo.save_invoice(invoice)


class HandleSePayWebhookUseCase:
    """UseCase to handle incoming SePay Webhook notifications."""

    def __init__(self, repo: InvoiceRepository):
        self.repo = repo

    async def execute(self, webhook_data: dict, auth_token: str | None = None) -> bool:
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

        # 5. Phát sự kiện InvoicePaid
        if invoice.id:
            await EventBus.publish(
                InvoicePaid(
                    invoice_id=invoice.id,
                    user_id=invoice.user_id,
                    amount=invoice.amount,
                    reference_code=invoice.reference_code,
                    transaction_id=transaction_id,
                    paid_at=datetime.now(UTC),
                )
            )

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
        team_id: int | None = None,
        fund_code: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Invoice]:
        return self.repo.get_all_active(
            user_id=user_id,
            status=status,
            billing_period=billing_period,
            team_id=team_id,
            fund_code=fund_code,
            skip=skip,
            limit=limit,
        )

    def get_paged_invoices(
        self,
        user_id: int | None = None,
        status: str | None = None,
        billing_period: date | None = None,
        team_id: int | None = None,
        fund_code: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Invoice], int]:
        return self.repo.get_paged_active(
            user_id=user_id,
            status=status,
            billing_period=billing_period,
            team_id=team_id,
            fund_code=fund_code,
            search=search,
            page=page,
            page_size=page_size,
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

    def get_summary(
        self,
        billing_period: date | None = None,
        team_id: int | None = None,
        fund_code: str | None = None,
        user_id: int | None = None,
    ) -> dict[str, int]:
        return self.repo.get_summary(
            billing_period=billing_period,
            team_id=team_id,
            fund_code=fund_code,
            user_id=user_id,
        )


class QRGenerator:
    """Utility to generate VietQR URL for an invoice."""

    @staticmethod
    def _remove_accents(text: str) -> str:
        """Chuyển tiếng Việt có dấu thành không dấu, viết hoa."""
        if not text:
            return ""
        nfkd = unicodedata.normalize("NFKD", text)
        ascii_text = "".join(c for c in nfkd if not unicodedata.combining(c))
        ascii_text = ascii_text.replace("đ", "d").replace("Đ", "D")
        return ascii_text.upper().strip()

    @staticmethod
    def _format_user_name(user_name: str | None) -> str:
        """
        Chuẩn hóa tên thành viên:
        - Bỏ dấu, viết hoa.
        - Nếu độ dài <= 22 ký tự: Giữ nguyên họ tên.
        - Nếu độ dài > 22 ký tự: Lấy 2 từ cuối (Tên lót + Tên chính).
        """
        if not user_name:
            return ""
        user_name = re.sub(r"\(.*?\)", "", user_name)
        clean_name = QRGenerator._remove_accents(user_name)
        clean_name = re.sub(r"[^A-Z\s]", "", clean_name)
        clean_name = re.sub(r"\s+", " ", clean_name).strip()

        if not clean_name:
            return ""

        if len(clean_name) <= 22:
            return clean_name

        words = clean_name.split()
        if len(words) >= 2:
            short_name = f"{words[-2]} {words[-1]}"
            if len(short_name) <= 22:
                return short_name
            return words[-1][:22]
        return words[0][:22]

    @staticmethod
    def _format_description_or_type(invoice: Invoice) -> str:
        """
        Xác định phần mô tả/loại hóa đơn:
        - Nếu mô tả là "Hóa đơn tháng MM/YYYY": HD T{MM}/{YYYY} (ví dụ HD T10/2026)
        - Còn các trường hợp khác: map theo loại InvoiceItemType (VI PHAM, TIEN QUY, AN UONG, KHAC)
        """
        desc = invoice.description or ""
        clean_desc = QRGenerator._remove_accents(desc)

        # 1. Kiểm tra chính xác mẫu "Hóa đơn tháng MM/YYYY" (ví dụ: HOA DON THANG 10/2026)
        match = re.search(r"HOA\s+DON\s+THANG\s*(\d{1,2})[/_-](\d{4})", clean_desc)
        if match:
            month = match.group(1)
            year = match.group(2)
            return f"HD T{month}/{year}"

        match_month_only = re.search(r"HOA\s+DON\s+THANG\s*(\d{1,2})", clean_desc)
        if match_month_only and invoice.billing_period:
            month = match_month_only.group(1)
            return f"HD T{month}/{invoice.billing_period.year}"

        # 2. Các trường hợp khác: Map theo loại hóa đơn (InvoiceItemType)
        type_mapping = {
            InvoiceItemType.VIOLATION: "VI PHAM",
            InvoiceItemType.FUND: "TIEN QUY",
            InvoiceItemType.DINING: "AN UONG",
            InvoiceItemType.OTHER: "KHAC",
        }

        if invoice.items:
            seen_types: list[str] = []
            for item in invoice.items:
                mapped = type_mapping.get(item.item_type, "KHAC")
                if mapped not in seen_types:
                    seen_types.append(mapped)
            return " ".join(seen_types)

        return "KHAC"

    @classmethod
    def get_transfer_description(cls, invoice: Invoice) -> str:
        """Tạo nội dung chuyển khoản theo cú pháp [MÃ_HD] [TÊN] [MÔ_TẢ_HOẶC_LOẠI]."""
        ref_code = (invoice.reference_code or "").strip()
        user_name_part = cls._format_user_name(invoice.user_name)
        desc_part = cls._format_description_or_type(invoice)

        parts = [ref_code]
        if user_name_part:
            parts.append(user_name_part)
        if desc_part:
            parts.append(desc_part)

        transfer_des = " ".join(parts).strip()
        # Đảm bảo tối đa 48 ký tự an toàn cho Napas / VietQR
        return transfer_des[:48].strip()

    @classmethod
    def get_url(cls, invoice: Invoice) -> str:
        """Builds the SePay VietQR image URL."""
        base_url = "https://qr.sepay.vn/img"
        transfer_des = cls.get_transfer_description(invoice)
        params = {
            "bank": settings.SEPAY_BANK_CODE,
            "acc": settings.SEPAY_ACCOUNT_NO,
            "amount": invoice.amount,
            "des": transfer_des,
        }
        query_str = urllib.parse.urlencode(
            params,
            quote_via=lambda s, *args, **kwargs: urllib.parse.quote(str(s), safe="/"),
        )
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

    async def execute(
        self,
        month: int,
        year: int,
        team_id: int | None = None,
        fund_code: str = "DUT_AI",
        user_ids: list[int] = None,
        violation_price: int = 20000,
        fund_amount: int = 50000,
        extra_items: list[dict] = None,
        execute: bool = False,
    ) -> dict:
        if extra_items is None:
            extra_items = []
        if user_ids is None:
            user_ids = []

        team = None
        team_member_map = {}
        if team_id:
            team = self.team_repo.get_by_id_with_members(team_id)
            if team:
                team_member_map = {m.user_id: m.user_name for m in team.members}

        if not user_ids:
            raise BadRequestException(
                "Vui lòng chọn ít nhất 1 thành viên để tạo hóa đơn"
            )

        target_users = {}

        for uid in user_ids:
            target_users[uid] = team_member_map.get(uid, f"User #{uid}")

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
                    user_name=user_name,
                    fund_code=fund_code,
                    team_id=team_id,
                    amount=total_amount,
                    status=InvoiceStatus.PENDING,
                    description=description,
                    reference_code=ref,
                    billing_period=date(year, month, 1),
                    items=invoice_items,
                )

                saved = self.invoice_repo.save_invoice(invoice)
                created_invoices.append(saved)

                # Phát sự kiện InvoiceCreated
                if saved.id:
                    await EventBus.publish(
                        InvoiceCreated(
                            invoice_id=saved.id,
                            user_id=saved.user_id,
                            amount=saved.amount,
                            reference_code=saved.reference_code,
                            description=saved.description,
                            billing_period=saved.billing_period,
                        )
                    )

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
