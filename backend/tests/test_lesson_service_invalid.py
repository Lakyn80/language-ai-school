from app.modules.lessons.lesson_service import generate_lesson
from app.core.config import settings
import pytest


class DummyResponse:
    status_code = 200

    def json(self):
        return {
            "choices": [
                {
                    "message": {
                        "content": "THIS IS NOT JSON"
                    }
                }
            ]
        }


def test_invalid_json(monkeypatch):

    # ✅ mock API key
    monkeypatch.setattr(settings, "deepseek_api_key", "test-key")

    def fake_post(*args, **kwargs):
        return DummyResponse()

    monkeypatch.setattr("httpx.post", fake_post)

    result = generate_lesson("A1", "context")

    assert result["level"] == "A1"
    assert "story" in result
    assert "vocabulary" in result
    assert "questions" in result
    assert "writing_task" in result


class DummyErrorResponse:
    status_code = 401

    def json(self):
        return {
            "error": {
                "message": "Authentication Fails",
                "type": "authentication_error",
                "code": "invalid_request_error",
            }
        }


def test_api_error_raises_runtime_error(monkeypatch):
    monkeypatch.setattr(settings, "deepseek_api_key", "test-key")

    def fake_post(*args, **kwargs):
        return DummyErrorResponse()

    monkeypatch.setattr("httpx.post", fake_post)

    with pytest.raises(RuntimeError, match="DeepSeek API error"):
        generate_lesson("A1", "context")
