from fastapi import APIRouter

from app.pedagogy.comprehension.schemas import (
    ReadingEvaluateRequest,
    ReadingEvaluateResponse,
)
from app.pedagogy.comprehension.service import evaluate_reading

router = APIRouter()


@router.post(
    "/evaluate",
    response_model=ReadingEvaluateResponse,
)
def evaluate_reading_endpoint(payload: ReadingEvaluateRequest):
    return evaluate_reading(payload)
