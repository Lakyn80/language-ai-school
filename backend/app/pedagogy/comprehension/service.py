from .translation import translate_to_target_cached

from app.pedagogy.comprehension.evaluator import semantic_similarity
from app.pedagogy.comprehension.feedback import extract_missing_and_hallucinations
from app.pedagogy.comprehension.feedback_text import build_feedback_text
from app.pedagogy.cefr.scoring import evaluate_cefr_similarity

from .schemas import ReadingEvaluateRequest, ReadingEvaluateResponse


def evaluate_reading(payload: ReadingEvaluateRequest) -> ReadingEvaluateResponse:

    # -------------------------------------------------
    # 1. Translation
    # -------------------------------------------------

    translated_summary = translate_to_target_cached(
        payload.student_summary,
        payload.native_language,
        payload.target_language,
    )

    # -------------------------------------------------
    # 2. Semantic similarity
    # -------------------------------------------------

    similarity = semantic_similarity(
        payload.text,
        translated_summary,
    )

    # -------------------------------------------------
    # 3. Coverage analysis
    # -------------------------------------------------

    missing, hallucinations = extract_missing_and_hallucinations(
        original_text=payload.text,
        student_text=translated_summary,
    )

    total_sentences = max(
        payload.text.count("."),
        1
    )

    covered = total_sentences - len(missing)

    coverage_ratio = max(covered / total_sentences, 0.0)

    final_similarity = similarity * coverage_ratio

    # -------------------------------------------------
    # 4. CEFR scoring
    # -------------------------------------------------

    score, result = evaluate_cefr_similarity(
        payload.level,
        final_similarity,
    )

    # -------------------------------------------------
    # 5. Feedback
    # -------------------------------------------------

    feedback_native = build_feedback_text(
        native_language=payload.native_language,
        result=result,
        missing=missing,
        hallucinations=hallucinations,
    )

    return ReadingEvaluateResponse(
        score=int(final_similarity * 100),
        result=result,
        feedback_native=feedback_native,
        missing=missing,
        hallucinations=hallucinations,
    )
