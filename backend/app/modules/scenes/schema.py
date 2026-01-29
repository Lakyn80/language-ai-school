from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SceneBase(BaseModel):
    slug: str = Field(..., max_length=100)
    title: str = Field(..., max_length=200)
    description: str
    situation_text: str
    category: Optional[str] = None


class SceneCreate(SceneBase):
    pass


class SceneUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    situation_text: Optional[str] = None
    category: Optional[str] = None


class SceneOut(SceneBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
