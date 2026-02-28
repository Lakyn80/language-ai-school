from typing import Optional

import redis

from app.core.config import settings


_client: Optional[redis.Redis] = None
_memory_cache: dict[str, str] = {}


def _get_client() -> Optional[redis.Redis]:
    global _client
    if _client is not None:
        return _client

    try:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
        return _client
    except Exception:
        return None


def get_cached_translation(key: str) -> Optional[str]:
    client = _get_client()
    if client is not None:
        try:
            value = client.get(key)
            if value is not None:
                return str(value)
        except Exception:
            pass

    return _memory_cache.get(key)


def set_cached_translation(key: str, value: str) -> None:
    client = _get_client()
    if client is not None:
        try:
            client.set(key, value)
            return
        except Exception:
            pass

    _memory_cache[key] = value
