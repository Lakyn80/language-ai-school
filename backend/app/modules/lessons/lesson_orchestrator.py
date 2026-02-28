from app.core.config import settings
from app.modules.rag import search_rag
from app.modules.scenes import get_scene_by_slug
from .lesson_service import generate_lesson
from .persistence import store_lesson_generation
from .context_builder import build_lesson_context, scene_to_payload
from .cache.lesson_cache import get_cache
from .cache.cache_key import build_lesson_cache_key
from app.pedagogy.difficulty_engine import apply_difficulty_engine
from app.pedagogy.languages import get_language


ALLOWED_MODES = {"strict", "story", "cinematic"}
_MEMORY_REQUEST_CACHE: dict[tuple[str, str, str, str, str], dict] = {}


def load_scene(scene_id: str):
    return get_scene_by_slug(scene_id)


def generate_lesson_full(
    title_id: str,
    level: str,
    scene_id: str,
    mode: str = "strict",
    target_language: str = "en",
    native_language: str = "ru",
):
    if mode not in ALLOWED_MODES:
        allowed = ", ".join(sorted(ALLOWED_MODES))
        raise ValueError(f"Invalid mode '{mode}'. Allowed: {allowed}")

    target_lang = get_language(target_language)
    native_lang = get_language(native_language)

    request_cache_key = (
        title_id,
        scene_id,
        level,
        mode,
        target_language,
    )
    in_memory = _MEMORY_REQUEST_CACHE.get(request_cache_key)
    if in_memory is not None:
        return in_memory

    cache = get_cache()

    cache_scene_id = f"{scene_id}:{mode}:{target_language}"
    cache_key = build_lesson_cache_key(
        title_id=title_id,
        scene_id=cache_scene_id,
        level=level,
    )

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    rag_results = search_rag(title_id, k=5)

    scene = load_scene(scene_id)
    if scene is None:
        raise FileNotFoundError(f"Scene '{scene_id}' not found")

    scene_data = scene_to_payload(scene)
    full_context = build_lesson_context(
        rag_results=rag_results,
        scene_data=scene_data,
        target_lang=target_lang,
        native_lang=native_lang,
        mode=mode,
    )

    lesson = generate_lesson(level, full_context)
    difficulty = apply_difficulty_engine(lesson.get("story", ""), level)

    result = {
        "level": level,
        "mode": mode,
        "scene_id": scene_id,
        "target_language": target_language,
        "native_language": native_language,
        "scene": scene_data,
        "difficulty": difficulty,
        "context_used": rag_results,
        "lesson": lesson,
    }

    if settings.lessons_persist_generations:
        store_lesson_generation(
            level=level,
            input_context=full_context,
            result=result,
        )

    cache.set(cache_key, result)
    _MEMORY_REQUEST_CACHE[request_cache_key] = result
    return result
