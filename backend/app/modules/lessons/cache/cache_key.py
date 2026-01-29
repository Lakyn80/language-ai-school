import os
import hashlib


def build_lesson_cache_key(
    title_id: str,
    scene_id: str,
    level: str,
) -> str:
    version = os.getenv("LESSON_CACHE_VERSION", "1")

    raw = f"{title_id}:{scene_id}:{level}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    return f"lesson:v{version}:{digest}"
