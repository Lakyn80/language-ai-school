from typing import Any

from app.core.config import settings

from .schemas import ReadingEvaluateRequest, ReadingEvaluateResponse
from .workflows.legacy import run_legacy_reading_flow
from .workflows.langgraph_flow import (
    run_langgraph_reading_flow,
    run_langgraph_reading_flow_debug,
)


def run_reading_flow(
    payload: ReadingEvaluateRequest,
) -> ReadingEvaluateResponse:
    if settings.use_langgraph_reading:
        return run_langgraph_reading_flow(payload)

    return run_legacy_reading_flow(payload)


def run_reading_flow_debug(
    payload: ReadingEvaluateRequest,
) -> dict[str, Any]:
    return run_langgraph_reading_flow_debug(payload)
