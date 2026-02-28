from fastapi import APIRouter, Query, HTTPException
from .lesson_orchestrator import generate_lesson_full

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
        examples=["strict", "story", "cinematic"],
    ),
    target_language: str = Query(
        "en",
        description="Language being learned",
        examples=["en"],
    ),
    native_language: str = Query(
        "ru",
        description="Student native language",
        examples=["ru"],
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

    except RuntimeError as e:
        message = str(e).lower()
        status_code = 503 if "not configured" in message else 502
        raise HTTPException(status_code=status_code, detail=str(e))
