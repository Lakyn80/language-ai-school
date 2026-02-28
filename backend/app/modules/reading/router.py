from typing import Any

from fastapi import APIRouter

from .schemas import (
    ReadingEvaluateRequest,
    ReadingEvaluateResponse,
)
from .service import evaluate_reading_summary, evaluate_reading_summary_debug

router = APIRouter()


@router.post(
    "/evaluate",
    response_model=ReadingEvaluateResponse,
)
def evaluate_reading_endpoint(payload: ReadingEvaluateRequest):
    return evaluate_reading_summary(payload)


@router.post("/debug/evaluate")
def evaluate_reading_debug_endpoint(
    payload: ReadingEvaluateRequest,
) -> dict[str, Any]:
    return evaluate_reading_summary_debug(payload)
