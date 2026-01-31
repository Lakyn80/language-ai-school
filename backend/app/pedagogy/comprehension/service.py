import hashlib
import logging
import time

import httpx

from app.core.config import settings
from .schemas import ReadingEvaluateRequest, ReadingEvaluateResponse
from .evaluator import semantic_similarity


PASS_THRESHOLD = 0.65
CACHE_TTL_SECONDS = 2592000
MAX_TRANSLATION_ATTEMPTS = 3

logger = logging.getLogger(__name__)
_redis_client = None


def _get_redis_client():
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    try:
        import redis
        _redis_client = redis.Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
        return _redis_client
    except Exception as exc:
        logger.warning("Redis unavailable: %s", exc)
        return None


def _make_cache_key(text: str, target_language: str) -> str:
    digest = hashlib.sha256(
        f"{text}{target_language}".encode("utf-8")
    ).hexdigest()
    return f"translation:{digest}"


def translate_to_target(text: str, target_language: str) -> str:
    if not settings.deepseek_api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not configured")

    system_prompt = (
        "You are a translation engine. "
        "Translate the user's text into the target language. "
        "Return only the translated text, with no quotes or extra commentary. "
        f"Target language: {target_language}"
    )

    payload = {
        "model": settings.deepseek_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        "temperature": 0,
    }

    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }

    last_exc = None
    for attempt in range(MAX_TRANSLATION_ATTEMPTS):
        try:
            response = httpx.post(
                f"{settings.deepseek_base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120,
            )
            response.raise_for_status()

            translated = response.json()["choices"][0]["message"]["content"]
            return translated.strip()
        except Exception as exc:
            last_exc = exc
            if attempt < MAX_TRANSLATION_ATTEMPTS - 1:
                time.sleep(0.5 * (attempt + 1))
                continue
            raise last_exc


def translate_to_target_cached(text: str, target_language: str) -> str:
    cache_key = _make_cache_key(text, target_language)
    redis_client = _get_redis_client()

    if redis_client is not None:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                return cached
        except Exception as exc:
            logger.warning("Redis get failed: %s", exc)
            redis_client = None

    try:
        translated = translate_to_target(text, target_language)
    except Exception as exc:
        logger.error("DeepSeek translation failed: %s", exc)
        return text

    if not translated:
        logger.error("DeepSeek translation returned empty result")
        return text

    if redis_client is not None:
        try:
            redis_client.set(
                cache_key,
                translated,
                ex=CACHE_TTL_SECONDS,
            )
        except Exception as exc:
            logger.warning("Redis set failed: %s", exc)

    return translated


def evaluate_reading(payload: ReadingEvaluateRequest) -> ReadingEvaluateResponse:
    translated_summary = translate_to_target_cached(
        payload.student_summary,
        payload.target_language,
    )

    similarity = semantic_similarity(
        payload.text,
        translated_summary,
    )

    score = int(similarity * 100)

    result = "PASS" if similarity >= PASS_THRESHOLD else "FAIL"

    return ReadingEvaluateResponse(
        score=score,
        result=result,
        feedback_native="",
        missing=[],
        hallucinations=[],
    )
