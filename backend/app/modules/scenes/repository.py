from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Scene


def list_scenes(db: Session) -> list[Scene]:
    stmt = select(Scene).order_by(Scene.id)
    return db.execute(stmt).scalars().all()


def get_scene_by_slug(db: Session, slug: str) -> Scene | None:
    stmt = select(Scene).where(Scene.slug == slug)
    return db.execute(stmt).scalar_one_or_none()


def get_scene_by_id(db: Session, scene_id: int) -> Scene | None:
    stmt = select(Scene).where(Scene.id == scene_id)
    return db.execute(stmt).scalar_one_or_none()


def list_scene_slugs(db: Session) -> set[str]:
    return set(db.execute(select(Scene.slug)).scalars().all())


def create_scene(db: Session, data: dict) -> Scene:
    scene = Scene(**data)
    db.add(scene)
    db.commit()
    db.refresh(scene)
    return scene


def update_scene(db: Session, scene_id: int, data: dict) -> Scene | None:
    scene = get_scene_by_id(db, scene_id)
    if scene is None:
        return None

    for key, value in data.items():
        if value is not None:
            setattr(scene, key, value)

    db.add(scene)
    db.commit()
    db.refresh(scene)
    return scene


def delete_scene(db: Session, scene_id: int) -> Scene | None:
    scene = get_scene_by_id(db, scene_id)
    if scene is None:
        return None

    db.delete(scene)
    db.commit()
    return scene
