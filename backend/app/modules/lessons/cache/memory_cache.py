from typing import Optional
from app.modules.lessons.cache.lesson_cache import LessonCache


class MemoryLessonCache(LessonCache):
    def __init__(self):
        self._store: dict[str, dict] = {}

    def get(self, key: str) -> Optional[dict]:
        return self._store.get(key)

    def set(self, key: str, value: dict) -> None:
        self._store[key] = value
