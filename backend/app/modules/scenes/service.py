from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.scenes.models import Scene


def _get_session(db: Optional[Session]) -> tuple[Session, bool]:
    if db is None:
        from app.db.session import SessionLocal
        return SessionLocal(), True
    return db, False


def create_scene(data: dict, db: Optional[Session] = None) -> Scene:
    db, should_close = _get_session(db)
    try:
        scene = Scene(**data)
        db.add(scene)
        db.commit()
        db.refresh(scene)
        return scene
    finally:
        if should_close:
            db.close()


def get_scene_by_id(scene_id: int, db: Optional[Session] = None) -> Optional[Scene]:
    db, should_close = _get_session(db)
    try:
        stmt = select(Scene).where(Scene.id == scene_id)
        return db.execute(stmt).scalar_one_or_none()
    finally:
        if should_close:
            db.close()


def get_scene_by_slug(slug: str, db: Optional[Session] = None) -> Optional[Scene]:
    db, should_close = _get_session(db)
    try:
        stmt = select(Scene).where(Scene.slug == slug)
        return db.execute(stmt).scalar_one_or_none()
    finally:
        if should_close:
            db.close()


def list_scenes(db: Optional[Session] = None) -> list[Scene]:
    db, should_close = _get_session(db)
    try:
        stmt = select(Scene).order_by(Scene.id)
        return db.execute(stmt).scalars().all()
    finally:
        if should_close:
            db.close()


def update_scene(scene_id: int, data: dict, db: Optional[Session] = None) -> Optional[Scene]:
    db, should_close = _get_session(db)
    try:
        stmt = select(Scene).where(Scene.id == scene_id)
        scene = db.execute(stmt).scalar_one_or_none()
        if scene is None:
            return None

        for key, value in data.items():
            if value is not None:
                setattr(scene, key, value)

        db.add(scene)
        db.commit()
        db.refresh(scene)
        return scene
    finally:
        if should_close:
            db.close()


def delete_scene(scene_id: int, db: Optional[Session] = None) -> Optional[Scene]:
    db, should_close = _get_session(db)
    try:
        stmt = select(Scene).where(Scene.id == scene_id)
        scene = db.execute(stmt).scalar_one_or_none()
        if scene is None:
            return None

        db.delete(scene)
        db.commit()
        return scene
    finally:
        if should_close:
            db.close()
