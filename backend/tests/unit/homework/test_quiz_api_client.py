"""Unit tests for QuizApiClient authentication headers and MANAGE_API_KEY dependency."""

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.core.deps import _extract_manage_api_key, verify_manage_api_key
from app.homework.infrastructure.quiz_api import QuizApiClient


def test_quiz_api_client_includes_bearer_header_from_quiz_webhook_secret(monkeypatch):
    """Sends Authorization: Bearer <QUIZ_WEBHOOK_SECRET> when configured."""
    monkeypatch.setattr(settings, "QUIZ_WEBHOOK_SECRET", "  quiz-secret-xyz  ")
    client = QuizApiClient()

    headers = client._get_headers()

    assert headers == {
        "Content-Type": "application/json",
        "Authorization": "Bearer quiz-secret-xyz",
    }


def test_quiz_api_client_omits_authorization_header_when_secret_empty(monkeypatch):
    """Omits Authorization header when QUIZ_WEBHOOK_SECRET is empty or whitespace."""
    monkeypatch.setattr(settings, "QUIZ_WEBHOOK_SECRET", "   ")
    client = QuizApiClient()

    headers = client._get_headers()

    assert headers == {"Content-Type": "application/json"}
    assert "Authorization" not in headers


def test_extract_manage_api_key_supports_bearer_and_webhook_header():
    """Accepts MANAGE_API_KEY from Authorization Bearer or X-Webhook-Secret."""
    assert _extract_manage_api_key("Bearer sk-abc123", None) == "sk-abc123"
    assert _extract_manage_api_key("bearer   sk-abc123  ", None) == "sk-abc123"
    assert _extract_manage_api_key(None, "sk-abc123") == "sk-abc123"
    assert _extract_manage_api_key("Bearer sk-primary", "sk-fallback") == "sk-primary"
    assert _extract_manage_api_key("Basic invalid", "sk-fallback") == "sk-fallback"
    assert _extract_manage_api_key(None, None) is None


def test_verify_manage_api_key_accepts_valid_headers(monkeypatch):
    """Passes verification when MANAGE_API_KEY matches either supported header."""
    monkeypatch.setattr(settings, "MANAGE_API_KEY", "sk-valid-key")

    verify_manage_api_key(authorization="Bearer sk-valid-key", x_webhook_secret=None)
    verify_manage_api_key(authorization=None, x_webhook_secret="sk-valid-key")


def test_verify_manage_api_key_rejects_missing_or_invalid_key(monkeypatch):
    """Raises 401 when MANAGE_API_KEY is unconfigured, missing, or mismatched."""
    monkeypatch.setattr(settings, "MANAGE_API_KEY", "sk-valid-key")

    with pytest.raises(HTTPException) as exc1:
        verify_manage_api_key(authorization=None, x_webhook_secret=None)
    assert exc1.value.status_code == 401

    with pytest.raises(HTTPException) as exc2:
        verify_manage_api_key(authorization="Bearer sk-wrong", x_webhook_secret=None)
    assert exc2.value.status_code == 401

    monkeypatch.setattr(settings, "MANAGE_API_KEY", "")
    with pytest.raises(HTTPException) as exc3:
        verify_manage_api_key(authorization="Bearer sk-valid-key", x_webhook_secret=None)
    assert exc3.value.status_code == 401
