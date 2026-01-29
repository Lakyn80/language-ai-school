import json
import os
import redis
from typing import Optional

from app.modules.lessons.cache.lesson_cache import LessonCache


class RedisLessonCache(LessonCache):
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        ttl_seconds: int | None = None,
    ):
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
        )

        if ttl_seconds is None:
            ttl_seconds = int(
                os.getenv("LESSON_CACHE_TTL_SECONDS", "86400")
            )

        self.ttl_seconds = ttl_seconds

    def get(self, key: str) -> Optional[dict]:
        value = self.client.get(key)
        if value is None:
            return None
        return json.loads(value)

    def set(self, key: str, value: dict) -> None:
        self.client.set(
            key,
            json.dumps(value),
            ex=self.ttl_seconds,
        )
