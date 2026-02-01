import pytest

from app.pedagogy.cefr.scoring import evaluate_cefr_similarity
from app.pedagogy.comprehension.feedback_text import build_feedback_text


# -------------------------------------------------
# CEFR SCORING TESTS
# -------------------------------------------------

def test_a1_pass():
    score, result = evaluate_cefr_similarity("A1", 0.41)
    assert result == "PASS"
    assert score == 41


def test_a1_fail():
    score, result = evaluate_cefr_similarity("A1", 0.39)
    assert result == "FAIL"


def test_b1_threshold():
    score, result = evaluate_cefr_similarity("B1", 0.65)
    assert result == "PASS"


def test_b1_fail_below_threshold():
    score, result = evaluate_cefr_similarity("B1", 0.64)
    assert result == "FAIL"


def test_c2_strict_pass():
    score, result = evaluate_cefr_similarity("C2", 0.93)
    assert result == "PASS"


# -------------------------------------------------
# FEEDBACK TEXT TESTS
# -------------------------------------------------

def test_feedback_ru_pass():
    text = build_feedback_text(
        native_language="ru",
        result="PASS",
        missing=[],
        hallucinations=[],
    )
    assert "понял" in text.lower()


def test_feedback_ru_missing():
    text = build_feedback_text(
        native_language="ru",
        result="FAIL",
        missing=["something"],
        hallucinations=[],
    )
    assert "важн" in text.lower()


def test_feedback_cs_hallucination():
    text = build_feedback_text(
        native_language="cs",
        result="FAIL",
        missing=[],
        hallucinations=["x"],
    )
    assert "nebyl" in text.lower()


def test_feedback_fallback_to_en():
    text = build_feedback_text(
        native_language="de",
        result="PASS",
        missing=[],
        hallucinations=[],
    )
    assert "understood" in text.lower()
