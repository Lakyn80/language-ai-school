from typing import Any

from .schemas import ReadingEvaluateRequest, ReadingEvaluateResponse
from .flow import run_reading_flow, run_reading_flow_debug


def evaluate_reading_summary(
    payload: ReadingEvaluateRequest,
) -> ReadingEvaluateResponse:
    return run_reading_flow(payload)


def evaluate_reading_summary_debug(
    payload: ReadingEvaluateRequest,
) -> dict[str, Any]:
    return run_reading_flow_debug(payload)
