from .schemas import AdaptiveLessonRequest, AdaptiveLessonResponse
from .workflows import run_adaptive_langgraph_flow


def run_adaptive_flow(
    payload: AdaptiveLessonRequest,
) -> AdaptiveLessonResponse:
    return run_adaptive_langgraph_flow(payload)
