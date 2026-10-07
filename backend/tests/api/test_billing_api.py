"""
API Tests for Billing Controller (/api/v1/billing).
Covers success responses, 401 Unauthorized, 403 Forbidden, 404 Not Found, and 400 Bad Request.
"""

import pytest


def test_get_my_invoices_authenticated(member_client):
    """User đã đăng nhập có thể lấy danh sách hoá đơn của chính mình."""
    res = member_client.get("/api/v1/billing/me")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)


def test_get_my_invoices_unauthenticated_returns_401(unauth_client):
    """Chưa đăng nhập khi truy cập /billing/me phải trả về 401."""
    res = unauth_client.get("/api/v1/billing/me")
    assert res.status_code == 401


def test_get_all_invoices_as_admin_success(admin_client):
    """Admin có quyền BillingPermission.READ xem được toàn bộ hoá đơn."""
    res = admin_client.get("/api/v1/billing/")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)


def test_get_all_invoices_as_member_returns_403(member_client):
    """Member không có quyền xem hoá đơn toàn hệ thống (403 Forbidden)."""
    res = member_client.get("/api/v1/billing/")
    assert res.status_code == 403


def test_get_invoice_detail_as_member_returns_403(member_client):
    """Member không có quyền xem chi tiết hoá đơn qua route admin (403 Forbidden)."""
    res = member_client.get("/api/v1/billing/1")
    assert res.status_code == 403


def test_get_invoice_detail_not_found(admin_client):
    """Tìm hoá đơn với ID không tồn tại phải trả về 404 Not Found."""
    res = admin_client.get("/api/v1/billing/99999999")
    assert res.status_code == 404


def test_create_invoice_as_member_returns_403(member_client):
    """Member không có quyền tạo hoá đơn (403 Forbidden)."""
    payload = {
        "user_id": 1,
        "items": [{"name": "Quỹ tháng", "amount": 50000}],
    }
    res = member_client.post("/api/v1/billing/", json=payload)
    assert res.status_code == 403


def test_create_invoice_missing_fields_returns_422_or_400(admin_client):
    """Tạo hoá đơn thiếu dữ liệu bắt buộc (items rỗng hoặc sai format)."""
    payload = {"description": "Thiếu user_id và items"}
    res = admin_client.post("/api/v1/billing/", json=payload)
    assert res.status_code in [400, 422]


def test_update_invoice_as_member_returns_403(member_client):
    """Member không có quyền cập nhật hoá đơn (403 Forbidden)."""
    payload = {"description": "Update"}
    res = member_client.put("/api/v1/billing/1", json=payload)
    assert res.status_code == 403


def test_delete_invoice_as_member_returns_403(member_client):
    """Member không có quyền xoá hoá đơn (403 Forbidden)."""
    res = member_client.delete("/api/v1/billing/1")
    assert res.status_code == 403


def test_sepay_webhook_invalid_token(unauth_client):
    """SePay webhook không có token hoặc token sai trả về không khớp/lỗi."""
    payload = {
        "id": 12345,
        "gateway": "Vietcombank",
        "transactionDate": "2026-10-08 12:00:00",
        "accountNumber": "123456789",
        "subAccount": None,
        "code": None,
        "content": "Dong tien quy INV9999",
        "transferType": "in",
        "description": "Dong tien",
        "transferAmount": 50000,
        "referenceCode": "REF123",
        "accumulated": 50000,
    }
    res = unauth_client.post("/api/v1/billing/webhook/sepay", json=payload)
    # Use case ném BadRequestException 401 nếu webhook token không hợp lệ
    assert res.status_code == 401
    assert "Lỗi xác thực Webhook" in res.json()["message"]
