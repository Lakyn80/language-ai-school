from app.modules.lessons.lesson_service import generate_lesson
from app.core.config import settings


class DummyResponse:
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
