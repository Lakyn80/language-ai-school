from pydantic import BaseModel, Field

from app.modules.reading import ReadingEvaluateResponse


class VocabularyItem(BaseModel):
    word: str = Field(..., min_length=1)
    meaning: str = Field(..., min_length=1)


class AdaptiveLessonPayload(BaseModel):
    level: str
    story: str
    vocabulary: list[VocabularyItem]
    questions: list[str]
    writing_task: str
    drill: list[str] = Field(default_factory=list)


class AdaptiveLessonRequest(BaseModel):
    student_id: str = Field(..., min_length=1)
    title_id: str = Field(..., min_length=1)
    scene_id: str = Field(..., min_length=1)
    level: str = Field(..., min_length=2)
    mode: str = Field(default="strict")
    target_language: str = Field(default="en")
    native_language: str = Field(default="cs")
    text: str = Field(..., min_length=1)
    student_summary: str = Field(..., min_length=1)
    run_id: str | None = None


class AdaptiveLessonResponse(BaseModel):
    run_id: str
    branch: str
    resumed: bool = False
    reading: ReadingEvaluateResponse
    lesson: AdaptiveLessonPayload
    checkpoints: list[str] = Field(default_factory=list)
    generation_meta: dict = Field(default_factory=dict)
