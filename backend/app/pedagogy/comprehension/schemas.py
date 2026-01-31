from pydantic import BaseModel, Field


class ReadingEvaluateRequest(BaseModel):
    level: str = Field(..., description="CEFR level (A1..C2)")
    target_language: str = Field(..., description="Language of the text being read (e.g. en, es, de)")
    native_language: str = Field(..., description="Student native language for feedback (e.g. ru, cs)")
    text: str = Field(..., description="Generated story/text the student read")
    student_summary: str = Field(..., description="Student summary in native language")


class ReadingEvaluateResponse(BaseModel):
    score: int
    result: str  # PASS / FAIL
    feedback_native: str
    missing: list[str]
    hallucinations: list[str]
