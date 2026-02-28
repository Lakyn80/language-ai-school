from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.shared.database import get_db

from . import service
from .schema import SceneCreate, SceneUpdate, SceneOut


router = APIRouter()


@router.get("", response_model=list[SceneOut])
def list_scenes(db: Session = Depends(get_db)):
    return service.list_scenes(db=db)


@router.get("/{slug}", response_model=SceneOut)
def get_scene(slug: str, db: Session = Depends(get_db)):
    scene = service.get_scene_by_slug(slug, db=db)
    if scene is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found",
        )
    return scene


@router.post("", response_model=SceneOut, status_code=status.HTTP_201_CREATED)
def create_scene(scene_in: SceneCreate, db: Session = Depends(get_db)):
    return service.create_scene(scene_in.model_dump(), db=db)


@router.put("/{id}", response_model=SceneOut)
def update_scene(id: int, scene_in: SceneUpdate, db: Session = Depends(get_db)):
    scene = service.update_scene(
        id,
        scene_in.model_dump(exclude_unset=True),
        db=db,
    )
    if scene is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found",
        )
    return scene


@router.delete("/{id}", response_model=SceneOut)
def delete_scene(id: int, db: Session = Depends(get_db)):
    scene = service.delete_scene(id, db=db)
    if scene is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found",
        )
    return scene
