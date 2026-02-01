import hashlib
import logging
import time

import httpx

from app.core.config import settings
from app.pedagogy.comprehension.evaluator import semantic_similarity
from app.pedagogy.comprehension.feedback import extract_missing_and_hallucinations
from app.pedagogy.comprehension.feedback_text import build_feedback_text
from app.pedagogy.cefr.scoring import evaluate_cefr_similarity

from .schemas import ReadingEvaluateRequest, ReadingEvaluateResponse


CACHE_TTL_SECONDS = 2592000
MAX_TRANSLATION_ATTEMPTS = 3
_redis_client = None
logger = logging.getLogger(__name__)


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


def translate_to_target(
    text: str,
    target_language: str,
    source_language: str | None = None,
) -> str:
    if not settings.deepseek_api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not configured")

    if source_language:
        direction = f"from {source_language} to {target_language}"
    else:
        direction = f"to {target_language}"

    system_prompt = (
        "You are a translation engine. "
        f"Translate the user's text {direction}. "
        "Return only the translated text, with no quotes or extra commentary."
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


def translate_to_target_cached(
    text: str,
    target_language: str,
    source_language: str | None = None,
) -> str:
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
        translated = translate_to_target(
            text=text,
            target_language=target_language,
            source_language=source_language,
        )
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
    """
    Reading comprehension evaluation pipeline:

    1. Student writes summary in native or target language
    2. Summary is translated into target language
    3. Semantic similarity is computed (target ↔ target)
    4. CEFR-based scoring (A1–C2)
    5. Missing information detection
    6. Hallucination detection
    7. Native-language feedback
    """

    # -------------------------------------------------
    # 1. Translation (Redis cache first)
    # -------------------------------------------------

    translated_summary = translate_to_target_cached(
        payload.student_summary,
        payload.target_language,
    )

    # -------------------------------------------------
    # 2. Semantic similarity
    # -------------------------------------------------

    similarity = semantic_similarity(
        payload.text,
        translated_summary,
    )

    # -------------------------------------------------
    # 3. CEFR scoring
    # -------------------------------------------------

    score, result = evaluate_cefr_similarity(
        level=payload.level,
        similarity=similarity,
    )

    # -------------------------------------------------
    # 4. Missing & hallucinations
    # -------------------------------------------------

    missing, hallucinations = extract_missing_and_hallucinations(
        original_text=payload.text,
        student_text=translated_summary,
    )

    # -------------------------------------------------
    # 5. Feedback text (native language)
    # -------------------------------------------------

    feedback_native = build_feedback_text(
        native_language=payload.native_language,
        result=result,
        missing=missing,
        hallucinations=hallucinations,
    )

    # -------------------------------------------------
    # 6. Response
    # -------------------------------------------------

    return ReadingEvaluateResponse(
        score=score,
        result=result,
        feedback_native=feedback_native,
        missing=missing,
        hallucinations=hallucinations,
    )
