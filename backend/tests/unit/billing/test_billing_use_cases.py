from datetime import date
from unittest.mock import MagicMock

import pytest

from app.billing.application.use_cases import (
    CreateInvoiceUseCase,
    CreateMonthlyInvoicesUseCase,
    UpdateInvoiceUseCase,
)
from app.billing.domain.entity import (
    Invoice,
    InvoiceItemType,
    InvoiceStatus,
)
from app.shared.application.response import BadRequestException
from app.team.domain.entity import Team, TeamMemberInfo


def test_invoice_entity_requires_team_id():
    # Without team_id, should raise ValidationError
    with pytest.raises(Exception):
        Invoice(
            user_id=1,
            amount=50000,
            reference_code="DUT123456",
            billing_period=date(2026, 9, 1),
        )

    # With team_id, should succeed
    inv = Invoice(
        user_id=1,
        team_id=2,
        amount=50000,
        reference_code="DUT123456",
        billing_period=date(2026, 9, 1),
    )
    assert inv.team_id == 2


@pytest.mark.asyncio
async def test_create_monthly_invoices_requires_team_id():
    invoice_repo = MagicMock()
    violation_repo = MagicMock()
    team_repo = MagicMock()

    uc = CreateMonthlyInvoicesUseCase(invoice_repo, violation_repo, team_repo)

    # Missing or 0/None team_id raises BadRequestException
    with pytest.raises(BadRequestException) as exc_info:
        await uc.execute(month=9, year=2026, team_id=None)  # type: ignore
    assert "chọn nhóm" in str(exc_info.value.message).lower()


@pytest.mark.asyncio
async def test_create_monthly_invoices_with_team_id():
    invoice_repo = MagicMock()
    violation_repo = MagicMock()
    team_repo = MagicMock()

    mock_team = Team(
        id=5,
        team_name="Engineering",
        members=[
            TeamMemberInfo(user_id=10, user_name="Alice", email="alice@test.com"),
        ],
    )
    team_repo.get_by_id_with_members.return_value = mock_team
    violation_repo.get_by_month.return_value = []
    invoice_repo.save_invoice.side_effect = lambda inv: inv

    uc = CreateMonthlyInvoicesUseCase(invoice_repo, violation_repo, team_repo)

    result = await uc.execute(
        month=9,
        year=2026,
        team_id=5,
        user_ids=[10],
        execute=True,
    )

    assert len(result["invoices"]) == 1
    invoice = result["invoices"][0]
    assert invoice.team_id == 5
    assert invoice.user_id == 10
    assert invoice.amount == 50000

    # Also test empty user_ids raises error
    with pytest.raises(BadRequestException) as exc_info:
        await uc.execute(month=9, year=2026, team_id=5, user_ids=[])
    assert "chọn ít nhất 1 thành viên" in str(exc_info.value.message).lower()


@pytest.mark.asyncio
async def test_create_invoice_requires_team_id():
    invoice_repo = MagicMock()
    uc = CreateInvoiceUseCase(invoice_repo)

    with pytest.raises(BadRequestException) as exc_info:
        await uc.execute(
            items_data=[{"item_type": "FUND", "amount": 50000}],
            billing_period=date(2026, 9, 1),
            user_id=1,
            team_id=0,  # invalid
        )
    assert "chọn nhóm" in str(exc_info.value.message).lower()


def test_update_invoice_custom_violation_amount():
    invoice_repo = MagicMock()
    existing_invoice = Invoice(
        id=1,
        user_id=10,
        team_id=5,
        amount=20000,
        reference_code="DUT123456",
        billing_period=date(2026, 9, 1),
        status=InvoiceStatus.PENDING,
    )
    invoice_repo.get_by_id.return_value = existing_invoice
    invoice_repo.save_invoice.side_effect = lambda inv: inv

    uc = UpdateInvoiceUseCase(invoice_repo)
    updated = uc.execute(
        invoice_id=1,
        items_data=[{"item_type": "VIOLATION", "amount": 10000, "note": "Test Violation"}],
    )

    assert updated.amount == 10000
    assert len(updated.items) == 1
    assert updated.items[0].amount == 10000
    assert updated.items[0].item_type == InvoiceItemType.VIOLATION


@pytest.mark.asyncio
async def test_create_invoice_custom_violation_amount():
    invoice_repo = MagicMock()
    invoice_repo.save_invoice.side_effect = lambda inv: inv

    uc = CreateInvoiceUseCase(invoice_repo)
    invoices = await uc.execute(
        items_data=[{"item_type": "VIOLATION", "amount": 10000, "note": "Custom"}],
        billing_period=date(2026, 9, 1),
        user_id=1,
        team_id=5,
    )

    assert len(invoices) == 1
    assert invoices[0].amount == 10000
    assert invoices[0].items[0].amount == 10000


if __name__ == "__main__":
    test_invoice_entity_requires_team_id()
    test_update_invoice_custom_violation_amount()
    print("All sync billing use case tests passed!")
