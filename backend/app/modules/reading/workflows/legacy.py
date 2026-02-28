from app.pedagogy.comprehension import evaluate_reading

from ..schemas import ReadingEvaluateRequest, ReadingEvaluateResponse


def run_legacy_reading_flow(
    payload: ReadingEvaluateRequest,
) -> ReadingEvaluateResponse:
    return evaluate_reading(payload)
