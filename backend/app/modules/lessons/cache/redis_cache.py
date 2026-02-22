import redis
import json
import os

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True,
)

def _key(text: str, src: str, tgt: str) -> str:
    return f"translation:{src}:{tgt}:{hash(text)}"

def get_cached_translation(text: str, src: str, tgt: str) -> str | None:
    value = _client.get(_key(text, src, tgt))
    return value

def set_cached_translation(text: str, src: str, tgt: str, translated: str) -> None:
    _client.set(_key(text, src, tgt), translated)
