from app.modules.rag.service import search_rag
from app.modules.lessons.lesson_service import generate_lesson
from app.modules.lessons.scenes.scene_loader import load_scene
from app.modules.lessons.cache.lesson_cache import get_cache
from app.modules.lessons.cache.cache_key import build_lesson_cache_key


def generate_lesson_full(title_id: str, level: str, scene_id: str):

    cache = get_cache()

    cache_key = build_lesson_cache_key(
        title_id=title_id,
        scene_id=scene_id,
        level=level,
    )

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    rag_results = search_rag(title_id, k=5)

    scene = load_scene(scene_id)

    context_blocks = []

    texts = [
        item["text"]
        for item in rag_results
        if isinstance(item, dict) and "text" in item
    ]
    context_blocks.extend(texts)

    context_blocks.append(
        f"""
SCENE:
Location: {scene["location"]}
Goal: {scene["learning_goal"]}
Grammar: {", ".join(scene["grammar_targets"])}
Vocabulary: {", ".join(scene["vocabulary_core"])}
Dialogue roles: {", ".join(scene["dialogue_roles"])}
"""
    )

    full_context = "\n\n".join(context_blocks)

    lesson = generate_lesson(level, full_context)

    result = {
        "level": level,
        "scene_id": scene_id,
        "scene": scene,
        "context_used": rag_results,
        "lesson": lesson,
    }

    cache.set(cache_key, result)

    return result
