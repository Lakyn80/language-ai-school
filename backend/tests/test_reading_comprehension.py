from fastapi.testclient import TestClient
from unittest.mock import patch

from app.core.app_factory import create_app
from app.pedagogy.comprehension.translation import build_translation_cache_key

client = TestClient(create_app())


def fake_translate(text: str, source_language: str, target_language: str) -> str:
    return "He was flying to Berlin and went to the airport."


def fake_similarity(a: str, b: str) -> float:
    return 0.74


@patch("app.pedagogy.comprehension.service.translate_to_target_cached", new=fake_translate)
@patch("app.pedagogy.comprehension.service.semantic_similarity", new=fake_similarity)
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


@patch("app.pedagogy.comprehension.service.translate_to_target_cached", new=fake_translate)
@patch("app.pedagogy.comprehension.service.semantic_similarity", new=fake_similarity)
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
    source_lang = "ru"
    target_lang = "en"

    key1 = build_translation_cache_key(text, source_lang, target_lang)
    key2 = build_translation_cache_key(text, source_lang, target_lang)

    assert key1 == key2
    assert key1.startswith("tr:")
