"""
API Integration tests for Adaptive Datetime Ingestion.
Verifies that naive datetime strings sent from Frontend (in Vietnam local time)
are automatically parsed and stored as standard UTC in Meeting and Homework APIs.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_quiz_api_metadata():
    """Mock QuizApiClient.get_lesson_metadata để không phụ thuộc Quiz network API."""
    with patch(
        "app.homework.infrastructure.quiz_api.QuizApiClient.get_lesson_metadata",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = {
            "name": "Mocked Quiz Lesson",
            "has_coding": True,
            "has_game": True,
        }
        yield mock_get


def test_meeting_create_with_naive_vietnam_time_string(admin_client):
    """Client gửi chuỗi naive 19:30 giờ VN, backend tự động lưu và trả về mốc 12:30 UTC."""
    payload = {
        "title": "Buổi sinh hoạt kiểm thử Datetime Ingestion",
        "content": "Kiểm thử tự động hóa múi giờ",
        "start_time": "2026-10-31T19:30:00",
        "end_time": "2026-10-31T21:30:00",
        "require_check_in": False,
        "enable_evaluation": False,
        "user_ids": [],
    }

    res = admin_client.post("/api/v1/meetings", json=payload)
    assert res.status_code in (200, 201)
    data = res.json()["data"]

    # Verify start_time stored is 12:30 UTC (which corresponds to 19:30 VN)
    start_time_str = data["start_time"]
    parsed_start = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))

    # 19:30 in Vietnam (UTC+7) MUST be 12:30 in UTC
    assert parsed_start.hour == 12
    assert parsed_start.minute == 30

    # Cleanup
    meeting_id = data["id"]
    admin_client.delete(f"/api/v1/meetings/{meeting_id}")


def test_homework_create_with_naive_vietnam_time_string(admin_client, mock_current_user):
    """Client gửi deadline naive 23:59 giờ VN, backend tự động lưu mốc 16:59 UTC."""
    import uuid

    unique_slug = f"test-slug-{uuid.uuid4().hex[:8]}"
    payload = {
        "title": "Bài tập kiểm thử Datetime Ingestion",
        "deadline": "2026-11-05T23:59:00",
        "link": f"https://quiz.example.com/lessons/{unique_slug}",
        "slug": unique_slug,
        "requires_coding": True,
        "requires_game": True,
        "assignee_ids": [mock_current_user.id],
    }

    res = admin_client.post("/api/v1/homeworks", json=payload)
    assert res.status_code in (200, 201)
    data = res.json()["data"]

    # Verify deadline stored is 16:59 UTC (which corresponds to 23:59 VN)
    deadline_str = data["deadline"]
    parsed_deadline = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))

    # 23:59 in Vietnam (UTC+7) MUST be 16:59 in UTC
    assert parsed_deadline.hour == 16
    assert parsed_deadline.minute == 59

    # Cleanup
    hw_id = data["id"]
    admin_client.delete(f"/api/v1/homeworks/{hw_id}")
