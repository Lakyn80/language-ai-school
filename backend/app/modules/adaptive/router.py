from fastapi import APIRouter

from .schemas import AdaptiveLessonRequest, AdaptiveLessonResponse
from .service import run_adaptive_lesson

router = APIRouter()


@router.post(
    "/lesson",
    response_model=AdaptiveLessonResponse,
    summary="Run adaptive tutor workflow for one lesson",
)
def adaptive_lesson_endpoint(
    payload: AdaptiveLessonRequest,
) -> AdaptiveLessonResponse:
    return run_adaptive_lesson(payload)
