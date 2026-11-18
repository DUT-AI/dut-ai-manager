"""Unit tests for QuizApiClient authentication headers."""

from app.homework.infrastructure.quiz_api import QuizApiClient


def test_quiz_api_client_includes_bearer_header_when_api_key_set():
    """Sends Authorization: Bearer <QUIZ_API_KEY> when api_key is provided."""
    client = QuizApiClient()

    headers = client._get_headers()

    assert headers == {
        "Content-Type": "application/json",
        "Authorization": "Bearer test-key-123",
    }


def test_quiz_api_client_omits_authorization_header_when_api_key_empty():
    """Omits Authorization header when api_key is empty or whitespace."""
    client = QuizApiClient()

    headers = client._get_headers()

    assert headers == {"Content-Type": "application/json"}
    assert "Authorization" not in headers
