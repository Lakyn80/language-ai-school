from typing import Optional

from app.core.config import settings


class LessonCache:
    def get(self, key: str) -> Optional[dict]:
        raise NotImplementedError

    def set(self, key: str, value: dict) -> None:
        raise NotImplementedError


_default_cache: LessonCache | None = None


def get_cache() -> LessonCache:
    global _default_cache
    if _default_cache is not None:
        return _default_cache

    if settings.lessons_cache_backend == "redis":
        try:
            from .redis_cache import RedisLessonCache

            _default_cache = RedisLessonCache(settings.redis_url)
        except Exception:
            from .memory_cache import MemoryLessonCache

            _default_cache = MemoryLessonCache()
    else:
        from .memory_cache import MemoryLessonCache

        _default_cache = MemoryLessonCache()

    return _default_cache
