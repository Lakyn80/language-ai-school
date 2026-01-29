import json
from app.modules.lessons.lesson_service import generate_lesson
from app.core.config import settings


class DummyResponse:
    def json(self):
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "level": "A2",
                            "story": "Story.",
                            "vocabulary": [
                                {"word": "dog", "meaning": "animal"}
                            ],
                            "questions": ["Question?"],
                            "writing_task": "Write text."
                        })
                    }
                }
            ]
        }


def test_valid_llm_response(monkeypatch):

    # ✅ mock API key
    monkeypatch.setattr(settings, "deepseek_api_key", "test-key")

    def fake_post(*args, **kwargs):
        return DummyResponse()

    monkeypatch.setattr("httpx.post", fake_post)

    result = generate_lesson("A2", "context")

    assert result["level"] == "A2"
    assert result["story"] == "Story."
    assert len(result["vocabulary"]) == 1
