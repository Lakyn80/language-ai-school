from fastapi import APIRouter
from .service import health_check

router = APIRouter()


@router.get("/")
def health():
    return health_check()
