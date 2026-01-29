from pydantic import BaseModel
from typing import Dict


class RAGDocument(BaseModel):
    id: str
    text: str
    metadata: Dict
