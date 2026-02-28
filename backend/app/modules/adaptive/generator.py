import json
import logging
import random
import time
from collections import deque
from threading import Lock
from typing import Any

import httpx

from app.core.config import settings

from .schemas import AdaptiveLessonPayload

LOGGER = logging.getLogger(__name__)

_DEEPSEEK_RETRY_ATTEMPTS = 4
_DEEPSEEK_BASE_DELAY_SECONDS = 0.5
_DEEPSEEK_MAX_DELAY_SECONDS = 8.0
_DEEPSEEK_JITTER_SECONDS = 0.25

_FAIL_RATE_WINDOW = 100
_FAIL_RATE_ALERT_THRESHOLD = 0.30
_FAIL_RATE_MIN_SAMPLES = 20
_ALERT_COOLDOWN_SECONDS = 60.0

_MONITOR_LOCK = Lock()
_DEEPSEEK_ATTEMPT_HISTORY: deque[int] = deque(maxlen=_FAIL_RATE_WINDOW)
_LAST_ALERT_AT = 0.0

_LAST_VALID_LESSON_CACHE: dict[str, dict[str, Any]] = {}


def _build_context_block(
    rag_context: list[dict[str, Any]],
    scene_data: dict[str, Any],
    student_history: dict[str, Any],
) -> str:
    chunks = [
        item.get("text", "")
        for item in rag_context
        if isinstance(item, dict) and item.get("text")
    ]
    world_context = "\n\n".join(chunks) if chunks else "No RAG context found."

    history_records = student_history.get("records", [])
    recent_records = history_records[-3:] if isinstance(history_records, list) else []
    history_text = json.dumps(recent_records, ensure_ascii=False)

    return (
        f"WORLD CONTEXT:\n{world_context}\n\n"
        f"SCENE:\n{json.dumps(scene_data, ensure_ascii=False)}\n\n"
        f"STUDENT HISTORY (last 3):\n{history_text}"
    )


def _build_difficulty_block(cefr_rules: dict[str, Any]) -> str:
    return (
        f"CEFR LEVEL: {cefr_rules.get('level', 'A1')}\n"
        f"- max_words_per_sentence: {cefr_rules.get('max_sentence_words', 8)}\n"
        f"- allowed_tenses: {', '.join(cefr_rules.get('allowed_tenses', []))}\n"
        f"- allow_passive: {cefr_rules.get('allow_passive', False)}\n"
        f"- allow_conditionals: {cefr_rules.get('allow_conditionals', False)}\n"
        f"- allow_subordinate_clauses: {cefr_rules.get('allow_subordinate_clauses', False)}"
    )


def _build_task_block(branch: str, reading_result: dict[str, Any]) -> str:
    if branch == "PASS":
        return (
            "Student passed comprehension. Generate a more challenging continuation "
            "for the same world and scene."
        )

    missing = reading_result.get("missing", [])
    hallucinations = reading_result.get("hallucinations", [])
    return (
        "Student failed comprehension. Generate a simpler version of the lesson and "
        "add focused drill items. Prioritize missing facts and incorrect statements.\n"
        f"missing={json.dumps(missing, ensure_ascii=False)}\n"
        f"hallucinations={json.dumps(hallucinations, ensure_ascii=False)}"
    )


def _system_prompt(
    branch: str,
    context_block: str,
    difficulty_block: str,
    task_block: str,
) -> str:
    return f"""
SYSTEM:
You are an English tutor following strict CEFR rules.

CONTEXT:
{context_block}

DIFFICULTY RULES:
{difficulty_block}

TASK:
{task_block}

Return JSON only:
{{
  "story": "...",
  "vocabulary": [{{"word": "string", "meaning": "string"}}],
  "questions": ["string"],
  "writing_task": "...",
  "drill": ["string"]
}}
""".strip()


def _call_deepseek(
    model_name: str,
    system_prompt: str,
    retry_mode: bool,
) -> dict[str, Any]:
    user_prompt = (
        "Return strict JSON. No markdown. No extra keys."
        if retry_mode
        else "Return the JSON lesson now."
    )
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1 if retry_mode else 0.3,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }

    for attempt_index in range(_DEEPSEEK_RETRY_ATTEMPTS):
        try:
            response = httpx.post(
                f"{settings.deepseek_base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120,
            )
        except Exception as exc:
            _record_deepseek_attempt(False)
            if _is_retryable_exception(exc) and _can_retry(attempt_index):
                _sleep_with_backoff(attempt_index)
                continue
            raise RuntimeError(f"DeepSeek request failed: {exc}") from exc

        if response.status_code >= 500:
            _record_deepseek_attempt(False)
            if _can_retry(attempt_index):
                _sleep_with_backoff(attempt_index)
                continue
            raise RuntimeError(f"DeepSeek API error ({response.status_code}): {response.text}")

        try:
            data = response.json()
        except ValueError as exc:
            _record_deepseek_attempt(False)
            raise RuntimeError("DeepSeek returned non-JSON response") from exc

        if response.status_code >= 400:
            _record_deepseek_attempt(False)
            error = data.get("error", data)
            raise RuntimeError(f"DeepSeek API error ({response.status_code}): {error}")

        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            _record_deepseek_attempt(False)
            raise RuntimeError("DeepSeek response is missing 'choices'")

        first = choices[0] if isinstance(choices[0], dict) else {}
        message = first.get("message", {}) if isinstance(first, dict) else {}
        content = message.get("content")
        if not isinstance(content, str):
            _record_deepseek_attempt(False)
            raise RuntimeError("DeepSeek response is missing message content")

        monitor = _record_deepseek_attempt(True)
        return {
            "content": content,
            "http_attempts": attempt_index + 1,
            "monitor": monitor,
        }

    raise RuntimeError("DeepSeek retry limit reached")


def _can_retry(attempt_index: int) -> bool:
    return attempt_index < (_DEEPSEEK_RETRY_ATTEMPTS - 1)


def _sleep_with_backoff(attempt_index: int) -> None:
    delay = min(
        _DEEPSEEK_BASE_DELAY_SECONDS * (2**attempt_index),
        _DEEPSEEK_MAX_DELAY_SECONDS,
    )
    delay += random.uniform(0.0, _DEEPSEEK_JITTER_SECONDS)
    time.sleep(delay)


def _is_retryable_exception(exc: Exception) -> bool:
    if isinstance(exc, httpx.TimeoutException):
        return True

    if isinstance(exc, httpx.TransportError):
        lowered = str(exc).lower()
        dns_markers = (
            "name resolution",
            "temporary failure in name resolution",
            "nodename nor servname provided",
            "getaddrinfo failed",
        )
        return any(marker in lowered for marker in dns_markers)

    return False


def _record_deepseek_attempt(success: bool) -> dict[str, Any]:
    global _LAST_ALERT_AT
    with _MONITOR_LOCK:
        _DEEPSEEK_ATTEMPT_HISTORY.append(1 if success else 0)

        total = len(_DEEPSEEK_ATTEMPT_HISTORY)
        success_count = sum(_DEEPSEEK_ATTEMPT_HISTORY)
        fail_count = total - success_count
        fail_rate = (fail_count / total) if total else 0.0

        alert = False
        now = time.time()
        if (
            total >= _FAIL_RATE_MIN_SAMPLES
            and fail_rate >= _FAIL_RATE_ALERT_THRESHOLD
            and (now - _LAST_ALERT_AT) >= _ALERT_COOLDOWN_SECONDS
        ):
            LOGGER.error(
                "DeepSeek fail-rate alert: %.2f%% (%s/%s)",
                fail_rate * 100.0,
                fail_count,
                total,
            )
            _LAST_ALERT_AT = now
            alert = True

        return {
            "window_size": total,
            "fail_count": fail_count,
            "fail_rate": round(fail_rate, 4),
            "alert": alert,
        }


def _fallback_drill(reading_result: dict[str, Any]) -> list[str]:
    drill: list[str] = []
    for sentence in reading_result.get("missing", [])[:3]:
        if isinstance(sentence, str) and sentence.strip():
            drill.append(f"Retell correctly: {sentence.strip()}")

    if drill:
        return drill

    return [
        "Use short sentences in present simple.",
        "Include key facts from the text.",
        "Do not add information that is not in the text.",
    ]


def _fallback_lesson(
    level: str,
    branch: str,
    scene_data: dict[str, Any],
    reading_result: dict[str, Any],
) -> AdaptiveLessonPayload:
    location = scene_data.get("location") or "the scene"
    goal = scene_data.get("learning_goal") or "the lesson goal"
    core_vocab = scene_data.get("vocabulary_core", [])

    if branch == "PASS":
        story = (
            f"You are still in {location}. Continue the task and add one new problem. "
            "Keep the same world and raise difficulty slightly."
        )
    else:
        story = (
            f"You are in {location}. Use simple, short sentences. Focus on {goal}. "
            "Repeat the key facts clearly."
        )

    vocabulary = [
        {"word": word, "meaning": f"{word} in context"}
        for word in core_vocab[:7]
        if isinstance(word, str) and word.strip()
    ]
    if not vocabulary:
        vocabulary = [{"word": "lesson", "meaning": "a learning unit"}]

    questions = [
        "What is the main situation?",
        "What is the key action?",
        "What should the student remember?",
    ]

    writing_task = (
        "Write 4 short sentences with the key facts."
        if branch == "FAIL"
        else "Write 6 sentences continuing this situation."
    )

    return AdaptiveLessonPayload(
        level=level.upper(),
        story=story,
        vocabulary=vocabulary,
        questions=questions,
        writing_task=writing_task,
        drill=[] if branch == "PASS" else _fallback_drill(reading_result),
    )


def generate_adaptive_lesson(
    level: str,
    branch: str,
    rag_context: list[dict[str, Any]],
    scene_data: dict[str, Any],
    student_history: dict[str, Any],
    cefr_rules: dict[str, Any],
    reading_result: dict[str, Any],
    cache_key: str | None = None,
) -> dict[str, Any]:
    context_block = _build_context_block(rag_context, scene_data, student_history)
    difficulty_block = _build_difficulty_block(cefr_rules)
    task_block = _build_task_block(branch, reading_result)
    system_prompt = _system_prompt(
        branch=branch,
        context_block=context_block,
        difficulty_block=difficulty_block,
        task_block=task_block,
    )

    attempts: list[dict[str, Any]] = []
    monitor_snapshot: dict[str, Any] = {}
    models_to_try = [settings.deepseek_model, "deepseek-chat"]
    deduplicated_models: list[str] = []
    for model_name in models_to_try:
        if model_name and model_name not in deduplicated_models:
            deduplicated_models.append(model_name)

    if settings.deepseek_api_key:
        for model_name in deduplicated_models:
            for retry_mode in (False, True):
                try:
                    call_result = _call_deepseek(
                        model_name=model_name,
                        system_prompt=system_prompt,
                        retry_mode=retry_mode,
                    )
                    content = call_result["content"]
                    monitor_snapshot = call_result.get("monitor", {})
                    parsed = json.loads(content)
                    if not isinstance(parsed, dict):
                        raise RuntimeError("Generated payload is not an object")

                    parsed.setdefault("level", level.upper())
                    if branch == "FAIL" and not isinstance(parsed.get("drill"), list):
                        parsed["drill"] = _fallback_drill(reading_result)
                    if branch == "PASS" and "drill" not in parsed:
                        parsed["drill"] = []

                    lesson = AdaptiveLessonPayload(**parsed)
                    if cache_key:
                        _LAST_VALID_LESSON_CACHE[cache_key] = {
                            "lesson": lesson.model_dump(),
                            "model": model_name,
                        }
                    attempts.append(
                        {
                            "provider": "deepseek",
                            "model": model_name,
                            "retry_mode": retry_mode,
                            "http_attempts": call_result.get("http_attempts", 1),
                            "status": "ok",
                        }
                    )
                    return {
                        "lesson": lesson.model_dump(),
                        "attempts": attempts,
                        "provider": "deepseek",
                        "model": model_name,
                        "monitor": monitor_snapshot,
                    }
                except Exception as exc:
                    attempts.append(
                        {
                            "provider": "deepseek",
                            "model": model_name,
                            "retry_mode": retry_mode,
                            "status": "error",
                            "error": str(exc),
                        }
                    )

    if cache_key and cache_key in _LAST_VALID_LESSON_CACHE:
        cached = _LAST_VALID_LESSON_CACHE[cache_key]
        cached_lesson = AdaptiveLessonPayload(**cached["lesson"])
        return {
            "lesson": cached_lesson.model_dump(),
            "attempts": attempts,
            "provider": "cache_fallback",
            "model": str(cached.get("model", "cached")),
            "monitor": monitor_snapshot,
        }

    fallback = _fallback_lesson(
        level=level,
        branch=branch,
        scene_data=scene_data,
        reading_result=reading_result,
    )
    return {
        "lesson": fallback.model_dump(),
        "attempts": attempts,
        "provider": "local_fallback",
        "model": "template",
        "monitor": monitor_snapshot,
    }
