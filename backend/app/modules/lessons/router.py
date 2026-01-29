from fastapi import APIRouter
from app.modules.lessons.lesson_orchestrator import generate_lesson_full

router = APIRouter()


@router.get("/generate")
def generate_lesson(
    title_id: str,
    level: str,
    scene_id: str,
):
    return generate_lesson_full(title_id, level, scene_id)
