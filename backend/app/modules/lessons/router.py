from fastapi import APIRouter
from app.modules.lessons.service import generate_lesson_full

router = APIRouter()


@router.get("/generate")
def generate_lesson(title_id: str, level: str):
    return generate_lesson_full(title_id, level)
