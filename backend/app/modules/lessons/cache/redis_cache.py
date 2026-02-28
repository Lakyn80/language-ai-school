import json
from typing import Optional

import redis


class RedisLessonCache:
    def __init__(self, redis_url: str):
        self._client = redis.from_url(redis_url, decode_responses=True)

    def get(self, key: str) -> Optional[dict]:
        try:
            payload = self._client.get(key)
        except Exception:
            return None

        if payload is None:
            return None

        try:
            data = json.loads(payload)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            return None

        return None

    def set(self, key: str, value: dict) -> None:
        try:
            self._client.set(key, json.dumps(value, ensure_ascii=False))
        except Exception:
            return
