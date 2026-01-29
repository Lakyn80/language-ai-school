from app.modules.rag.service import search_rag
from app.modules.lessons.lesson_service import generate_lesson
from app.modules.lessons.cache.lesson_cache import get_cache
from app.modules.lessons.cache.cache_key import build_lesson_cache_key


def load_scene(scene_id: str):
    from app.modules.scenes.service import get_scene_by_slug
    return get_scene_by_slug(scene_id)


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
    if scene is None:
        raise FileNotFoundError(f"Scene '{scene_id}' not found")

    scene_data = scene
    if not isinstance(scene, dict):
        scene_data = {
            "location": getattr(scene, "slug", ""),
            "learning_goal": getattr(scene, "description", ""),
            "grammar_targets": [],
            "vocabulary_core": [],
            "dialogue_roles": [],
        }

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
Location: {scene_data["location"]}
Goal: {scene_data["learning_goal"]}
Grammar: {", ".join(scene_data["grammar_targets"])}
Vocabulary: {", ".join(scene_data["vocabulary_core"])}
Dialogue roles: {", ".join(scene_data["dialogue_roles"])}
"""
    )

    full_context = "\n\n".join(context_blocks)

    lesson = generate_lesson(level, full_context)

    result = {
        "level": level,
        "scene_id": scene_id,
        "scene": scene_data,
        "context_used": rag_results,
        "lesson": lesson,
    }

    cache.set(cache_key, result)

    return result
