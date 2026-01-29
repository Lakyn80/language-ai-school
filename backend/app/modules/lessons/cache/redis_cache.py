import json
import redis
from typing import Optional

from app.modules.lessons.cache.lesson_cache import LessonCache


class RedisLessonCache(LessonCache):
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
    ):
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
        )

    def get(self, key: str) -> Optional[dict]:
        value = self.client.get(key)
        if value is None:
            return None
        return json.loads(value)

    def set(self, key: str, value: dict) -> None:
        self.client.set(key, json.dumps(value))
