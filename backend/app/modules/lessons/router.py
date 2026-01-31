from fastapi import APIRouter, Query, HTTPException
from app.modules.lessons.lesson_orchestrator import generate_lesson_full

router = APIRouter()


@router.get(
    "/generate",
    summary="Generate lesson from world + scene",
)
def generate_lesson(
    title_id: str = Query(..., description="World / movie ID (e.g. secret_agent)"),
    scene_id: str = Query(..., description="Scene ID (e.g. restaurant_basic)"),
    level: str = Query(..., description="CEFR level (A1–C1)"),
    mode: str = Query(
        "strict",
        description="Generation mode",
        enum=["strict", "story", "cinematic"],
    ),
    target_language: str = Query(
        "en",
        description="Language being learned",
        example="en",
    ),
    native_language: str = Query(
        "ru",
        description="Student native language",
        example="ru",
    ),
):
    """
    Generates a language lesson.

    Example:

    - Russian student learning English:
      native_language=ru
      target_language=en

    - Czech student learning Russian:
      native_language=cs
      target_language=ru
    """

    try:
        return generate_lesson_full(
            title_id=title_id,
            scene_id=scene_id,
            level=level,
            mode=mode,
            target_language=target_language,
            native_language=native_language,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
