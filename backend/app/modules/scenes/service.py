from typing import Optional

from sqlalchemy.orm import Session

from app.shared.database import managed_session

from .models import Scene
from . import repository
from .seed import seed_default_scenes as _seed_default_scenes


def seed_default_scenes(db: Optional[Session] = None) -> int:
    with managed_session(db) as session:
        return _seed_default_scenes(session)


def create_scene(data: dict, db: Optional[Session] = None) -> Scene:
    with managed_session(db) as session:
        return repository.create_scene(session, data)


def get_scene_by_id(scene_id: int, db: Optional[Session] = None) -> Scene | None:
    with managed_session(db) as session:
        return repository.get_scene_by_id(session, scene_id)


def get_scene_by_slug(slug: str, db: Optional[Session] = None) -> Scene | None:
    with managed_session(db) as session:
        scene = repository.get_scene_by_slug(session, slug)
        if scene is not None:
            return scene

        _seed_default_scenes(session)
        return repository.get_scene_by_slug(session, slug)


def list_scenes(db: Optional[Session] = None) -> list[Scene]:
    with managed_session(db) as session:
        scenes = repository.list_scenes(session)
        if scenes:
            return scenes

        _seed_default_scenes(session)
        return repository.list_scenes(session)


def update_scene(scene_id: int, data: dict, db: Optional[Session] = None) -> Scene | None:
    with managed_session(db) as session:
        return repository.update_scene(session, scene_id, data)


def delete_scene(scene_id: int, db: Optional[Session] = None) -> Scene | None:
    with managed_session(db) as session:
        return repository.delete_scene(session, scene_id)
