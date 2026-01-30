from app.modules.rag.service import search_rag
from app.modules.lessons.lesson_service import generate_lesson
from app.modules.lessons.cache.lesson_cache import get_cache
from app.modules.lessons.cache.cache_key import build_lesson_cache_key
from app.pedagogy.difficulty_engine import apply_difficulty_engine
from app.pedagogy.languages import get_language


def load_scene(scene_id: str):
    from app.modules.scenes.service import get_scene_by_slug
    return get_scene_by_slug(scene_id)


def generate_lesson_full(
    title_id: str,
    level: str,
    scene_id: str,
    mode: str = "strict",
    target_language: str = "en",
    native_language: str = "ru",
):
    """
    mode:
      - strict
      - story
      - cinematic
    """

    target_lang = get_language(target_language)
    native_lang = get_language(native_language)

    cache = get_cache()

    cache_scene_id = f"{scene_id}:{mode}:{target_language}:{native_language}"

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

    if not isinstance(scene, dict):
        scene_data = {
            "location": getattr(scene, "slug", ""),
            "learning_goal": getattr(scene, "description", ""),
            "grammar_targets": [],
            "vocabulary_core": [],
            "dialogue_roles": [],
        }
    else:
        scene_data = scene

    # ---------- STYLE BLOCK ----------

    if mode == "cinematic":
        style_block = "CINEMATIC storytelling with dialogue and atmosphere."
    elif mode == "story":
        style_block = "Narrative storytelling with emotion."
    else:
        style_block = "STRICT language learning style."

    # ---------- CONTEXT ----------

    context_blocks = []

    texts = [
        item["text"]
        for item in rag_results
        if isinstance(item, dict) and "text" in item
    ]

    context_blocks.extend(texts)

    context_blocks.append(
        f"""
LANGUAGE SETTINGS:

TARGET LANGUAGE: {target_lang.name}
STUDENT NATIVE LANGUAGE: {native_lang.name}

Language properties:
- script: {target_lang.script}
- sentence order: {target_lang.sentence_order}
- articles: {target_lang.articles}
- cases: {target_lang.cases}
- genders: {target_lang.genders}

STYLE:
{style_block}

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

    difficulty = apply_difficulty_engine(
        lesson.get("story", ""),
        level,
    )

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

    cache.set(cache_key, result)
    return result
