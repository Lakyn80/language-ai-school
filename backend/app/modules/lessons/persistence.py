from typing import Optional

from sqlalchemy.orm import Session

from app.shared.database import managed_session

from . import repository
from .models import LessonGeneration


def store_lesson_generation(
    level: str,
    input_context: str,
    result: dict,
    db: Optional[Session] = None,
) -> Optional[LessonGeneration]:
    with managed_session(db) as session:
        try:
            return repository.create_lesson_generation(
                session,
                level=level,
                input_context=input_context,
                result=result,
            )
        except Exception:
            session.rollback()
            return None
