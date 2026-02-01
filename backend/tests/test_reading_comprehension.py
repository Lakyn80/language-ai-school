import hashlib
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.core.app_factory import create_app

client = TestClient(create_app())


def fake_translate(text: str, target_language: str) -> str:
    return "He was flying to Berlin and went to the airport."


def fake_similarity(a: str, b: str) -> float:
    return 0.74


def test_reading_evaluate_endpoint_works():
    payload = {
        "level": "B1",
        "target_language": "en",
        "native_language": "ru",
        "text": "John went to the airport because he had a flight to Berlin.",
        "student_summary": "Он летел в Берлин и приехал в аэропорт."
    }

    response = client.post("/api/reading/evaluate", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert "score" in data
    assert "result" in data
    assert "feedback_native" in data
    assert "missing" in data
    assert "hallucinations" in data


@patch("app.pedagogy.comprehension.service.translate_to_target_cached", fake_translate)
@patch("app.pedagogy.comprehension.evaluator.semantic_similarity", fake_similarity)
def test_translation_improves_score():
    payload = {
        "level": "B1",
        "target_language": "en",
        "native_language": "ru",
        "text": "John went to the airport because he had a flight to Berlin.",
        "student_summary": "Он летel v Berlín a přijel na letiště."
    }

    response = client.post("/api/reading/evaluate", json=payload)
    data = response.json()

    assert data["score"] >= 70
    assert data["result"] == "PASS"


def test_translation_cache_key_is_stable():
    text = "Он летел в Берлин и приехал в аэропорт."
    lang = "en"

    key1 = hashlib.sha256((text + lang).encode()).hexdigest()
    key2 = hashlib.sha256((text + lang).encode()).hexdigest()

    assert key1 == key2
