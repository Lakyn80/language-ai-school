import json
from pathlib import Path

from sqlalchemy.orm import Session

from .models import Scene
from .repository import list_scene_slugs

SCENES_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "scenes"


def _seed_row_from_payload(payload: dict) -> dict | None:
    scene_id = payload.get("scene_id")
    if not scene_id:
        return None

    title = payload.get("display_name") or scene_id.replace("_", " ").title()
    description = payload.get("learning_goal") or payload.get("description") or title

    return {
        "slug": scene_id,
        "title": title,
        "description": description,
        "situation_text": json.dumps(payload, ensure_ascii=False),
        "category": payload.get("level") or payload.get("category"),
    }


def seed_default_scenes(db: Session) -> int:
    files = sorted(SCENES_DATA_DIR.glob("*.json"))
    if not files:
        return 0

    existing_slugs = list_scene_slugs(db)
    created = 0

    for file in files:
        try:
            with file.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError):
            continue

        row = _seed_row_from_payload(payload)
        if row is None:
            continue

        if row["slug"] in existing_slugs:
            continue

        db.add(Scene(**row))
        existing_slugs.add(row["slug"])
        created += 1

    if created:
        db.commit()

    return created
