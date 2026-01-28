from pydantic import BaseModel
from typing import List


class TitleBase(BaseModel):
    id: str
    name: str
    universe: str
    language: str
    level: str
    description: str


class TitleList(BaseModel):
    titles: List[TitleBase]
