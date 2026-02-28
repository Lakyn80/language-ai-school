from .flow import run_adaptive_flow
from .schemas import AdaptiveLessonRequest, AdaptiveLessonResponse


def run_adaptive_lesson(
    payload: AdaptiveLessonRequest,
) -> AdaptiveLessonResponse:
    return run_adaptive_flow(payload)
