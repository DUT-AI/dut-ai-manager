from datetime import date

import pytest

from app.billing.application.use_cases import QRGenerator
from app.billing.domain.entity import (
    Invoice,
    InvoiceItem,
    InvoiceItemType,
    InvoiceStatus,
)


def test_qr_generator_monthly_invoice_normal_name():
    invoice = Invoice(
        id=1,
        user_id=10,
        user_name="Đỗ Hữu Minh Trí",
        team_id=2,
        amount=80000,
        status=InvoiceStatus.PENDING,
        description="Hóa đơn tháng 10/2026",
        reference_code="DUTU7PGC5",
        billing_period=date(2026, 10, 1),
        items=[
            InvoiceItem(item_type=InvoiceItemType.FUND, amount=50000),
            InvoiceItem(item_type=InvoiceItemType.VIOLATION, amount=30000),
        ],
    )
    des = QRGenerator.get_transfer_description(invoice)
    assert des == "DUTU7PGC5 DO HUU MINH TRI HD T10/2026"
    assert len(des) <= 48

    url = QRGenerator.get_url(invoice)
    assert "des=DUTU7PGC5%20DO%20HUU%20MINH%20TRI%20HD%20T10/2026" in url


def test_qr_generator_monthly_invoice_long_name():
    invoice = Invoice(
        id=2,
        user_id=11,
        user_name="Trương Thị Ngọc Huyền",
        team_id=2,
        amount=140000,
        status=InvoiceStatus.PENDING,
        description="Hóa đơn tháng 10/2026",
        reference_code="DUTRLZ4PY",
        billing_period=date(2026, 10, 1),
        items=[
            InvoiceItem(item_type=InvoiceItemType.FUND, amount=50000),
        ],
    )
    des = QRGenerator.get_transfer_description(invoice)
    # Tên <= 22 ký tự -> giữ nguyên: TRUONG THI NGOC HUYEN
    assert des == "DUTRLZ4PY TRUONG THI NGOC HUYEN HD T10/2026"
    assert len(des) <= 48


def test_qr_generator_monthly_invoice_extra_long_name():
    invoice = Invoice(
        id=22,
        user_id=111,
        user_name="Nguyễn Phước Hoàng Đình Nguyên",
        team_id=2,
        amount=140000,
        status=InvoiceStatus.PENDING,
        description="Hóa đơn tháng 10/2026",
        reference_code="DUTRLZ4PY",
        billing_period=date(2026, 10, 1),
        items=[
            InvoiceItem(item_type=InvoiceItemType.FUND, amount=50000),
        ],
    )
    des = QRGenerator.get_transfer_description(invoice)
    # Tên > 22 ký tự -> rút gọn thành 2 từ cuối: DINH NGUYEN
    assert des == "DUTRLZ4PY DINH NGUYEN HD T10/2026"
    assert len(des) <= 48


def test_qr_generator_dining_invoice():
    invoice = Invoice(
        id=3,
        user_id=12,
        user_name="Đặng Lâm Chí Vĩ",
        team_id=2,
        amount=50000,
        status=InvoiceStatus.PENDING,
        description="Phí After-Party WORKSHOP NCKH",
        reference_code="DUT4NOBCD",
        billing_period=date(2026, 8, 1),
        items=[
            InvoiceItem(item_type=InvoiceItemType.DINING, amount=50000),
        ],
    )
    des = QRGenerator.get_transfer_description(invoice)
    assert des == "DUT4NOBCD DANG LAM CHI VI AN UONG"
    assert len(des) <= 48


def test_qr_generator_violation_invoice():
    invoice = Invoice(
        id=4,
        user_id=13,
        user_name="Trần Đức Thắng",
        team_id=2,
        amount=20000,
        status=InvoiceStatus.PENDING,
        description="Phạt đi trễ họp ngày 15/10",
        reference_code="DUTMT93GT",
        billing_period=date(2026, 10, 1),
        items=[
            InvoiceItem(item_type=InvoiceItemType.VIOLATION, amount=20000),
        ],
    )
    des = QRGenerator.get_transfer_description(invoice)
    assert des == "DUTMT93GT TRAN DUC THANG VI PHAM"
    assert len(des) <= 48


def test_qr_generator_fund_invoice():
    invoice = Invoice(
        id=5,
        user_id=14,
        user_name="Phạm Lê Minh An",
        team_id=2,
        amount=50000,
        status=InvoiceStatus.PENDING,
        description="Đóng tiền quỹ bổ sung",
        reference_code="DUTEI744Q",
        billing_period=date(2026, 10, 1),
        items=[
            InvoiceItem(item_type=InvoiceItemType.FUND, amount=50000),
        ],
    )
    des = QRGenerator.get_transfer_description(invoice)
    assert des == "DUTEI744Q PHAM LE MINH AN TIEN QUY"
    assert len(des) <= 48


def test_qr_generator_description_has_month_word_but_not_hoa_don_thang():
    # Mô tả có chữ "tháng" nhưng không phải "Hóa đơn tháng" -> Phải lấy theo loại hóa đơn (TIEN QUY)
    invoice = Invoice(
        id=55,
        user_id=14,
        user_name="Phạm Lê Minh An",
        team_id=2,
        amount=50000,
        status=InvoiceStatus.PENDING,
        description="Đóng tiền quỹ tháng 10/2026",
        reference_code="DUTEI744Q",
        billing_period=date(2026, 10, 1),
        items=[
            InvoiceItem(item_type=InvoiceItemType.FUND, amount=50000),
        ],
    )
    des = QRGenerator.get_transfer_description(invoice)
    assert des == "DUTEI744Q PHAM LE MINH AN TIEN QUY"
    assert len(des) <= 48


def test_qr_generator_other_invoice():
    invoice = Invoice(
        id=6,
        user_id=15,
        user_name="Hà Thúc Toàn",
        team_id=2,
        amount=60000,
        status=InvoiceStatus.PENDING,
        description="Tiền mua đồng phục",
        reference_code="DUTSANPVA",
        billing_period=date(2026, 10, 1),
        items=[
            InvoiceItem(item_type=InvoiceItemType.OTHER, amount=60000),
        ],
    )
    des = QRGenerator.get_transfer_description(invoice)
    assert des == "DUTSANPVA HA THUC TOAN KHAC"
    assert len(des) <= 48


def test_qr_generator_missing_user_name():
    invoice = Invoice(
        id=7,
        user_id=16,
        user_name=None,
        team_id=2,
        amount=80000,
        status=InvoiceStatus.PENDING,
        description="Hóa đơn tháng 10/2026",
        reference_code="DUTU7PGC5",
        billing_period=date(2026, 10, 1),
        items=[],
    )
    des = QRGenerator.get_transfer_description(invoice)
    assert des == "DUTU7PGC5 HD T10/2026"


if __name__ == "__main__":
    test_qr_generator_monthly_invoice_normal_name()
    test_qr_generator_monthly_invoice_long_name()
    test_qr_generator_monthly_invoice_extra_long_name()
    test_qr_generator_dining_invoice()
    test_qr_generator_violation_invoice()
    test_qr_generator_fund_invoice()
    test_qr_generator_description_has_month_word_but_not_hoa_don_thang()
    test_qr_generator_other_invoice()
    test_qr_generator_missing_user_name()
    print("All QRGenerator tests passed successfully!")
