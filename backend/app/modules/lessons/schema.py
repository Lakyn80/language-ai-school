from pydantic import BaseModel, Field
from typing import List


class VocabularyItem(BaseModel):
    word: str = Field(..., min_length=1)
    meaning: str = Field(..., min_length=1)


class LessonResponse(BaseModel):
    level: str
    story: str
    vocabulary: List[VocabularyItem]
    questions: List[str]
    writing_task: str
