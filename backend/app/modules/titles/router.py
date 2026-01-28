from fastapi import APIRouter
from .service import load_titles

router = APIRouter()


@router.get("/")
def get_titles():
    return load_titles()
