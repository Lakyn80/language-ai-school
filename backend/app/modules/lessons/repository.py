import json

from sqlalchemy.orm import Session

from .models import LessonGeneration


def create_lesson_generation(
    db: Session,
    level: str,
    input_context: str,
    result: dict,
) -> LessonGeneration:
    row = LessonGeneration(
        level=level,
        input_context=input_context,
        result_json=json.dumps(result, ensure_ascii=False),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
