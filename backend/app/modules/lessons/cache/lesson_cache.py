from typing import Optional


class LessonCache:
    def get(self, key: str) -> Optional[dict]:
        raise NotImplementedError

    def set(self, key: str, value: dict) -> None:
        raise NotImplementedError


# default implementation
from app.modules.lessons.cache.memory_cache import MemoryLessonCache

_default_cache = MemoryLessonCache()


def get_cache() -> LessonCache:
    return _default_cache
