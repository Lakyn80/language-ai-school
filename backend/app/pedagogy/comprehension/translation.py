import hashlib

from app.modules.lessons.cache.redis_cache import _client


def build_translation_cache_key(
    source_text: str,
    source_lang: str,
    target_lang: str,
) -> str:
    payload = f"{source_lang}\n{target_lang}\n{source_text}".encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return f"tr:{digest}"


def translate_to_target(
    text: str,
    source_language: str,
    target_language: str,
) -> str:
    # stub – zatím žádný překlad
    # později: DeepSeek / OpenAI / NLLB
    return text


def translate_to_target_cached(
    text: str,
    source_language: str,
    target_language: str,
) -> str:
    key = build_translation_cache_key(text, source_language, target_language)
    cached = _client.get(key)
    if cached is not None:
        return cached

    translated = translate_to_target(text, source_language, target_language)
    _client.set(key, translated)
    return translated
