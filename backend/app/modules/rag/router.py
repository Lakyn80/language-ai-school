from fastapi import APIRouter
from pydantic import BaseModel
from app.modules.rag.service import search_rag

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    k: int = 3


@router.post("/search")
def rag_search(payload: SearchRequest):
    results = search_rag(payload.query, payload.k)
    return {
        "query": payload.query,
        "results": results
    }
