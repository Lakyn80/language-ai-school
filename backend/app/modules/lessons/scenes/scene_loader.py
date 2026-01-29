import json
from pathlib import Path
from app.core.config import settings


BASE_DIR = Path(__file__).resolve().parents[4]

SCENES_PATH = BASE_DIR / "app" / "data" / "scenes"


def load_scene(scene_id: str) -> dict:
    scene_file = SCENES_PATH / f"{scene_id}.json"

    if not scene_file.exists():
        raise FileNotFoundError(
            f"Scene '{scene_id}' not found at {scene_file}"
        )

    with open(scene_file, encoding="utf-8") as f:
        return json.load(f)
