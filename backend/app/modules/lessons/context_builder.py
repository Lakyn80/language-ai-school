import json
from typing import Any


def scene_to_payload(scene: dict | object) -> dict:
    if isinstance(scene, dict):
        raw = scene
    else:
        raw = {}
        situation_text = getattr(scene, "situation_text", None)
        if isinstance(situation_text, str) and situation_text.strip().startswith("{"):
            try:
                raw = json.loads(situation_text)
            except json.JSONDecodeError:
                raw = {}

        raw.setdefault("scene_id", getattr(scene, "slug", ""))
        raw.setdefault("display_name", getattr(scene, "title", ""))
        raw.setdefault("learning_goal", getattr(scene, "description", ""))
        raw.setdefault("location", getattr(scene, "slug", ""))

    return {
        "scene_id": raw.get("scene_id", ""),
        "display_name": raw.get("display_name", ""),
        "location": raw.get("location", raw.get("scene_id", "")),
        "learning_goal": raw.get("learning_goal", raw.get("description", "")),
        "grammar_targets": raw.get("grammar_targets", []),
        "vocabulary_core": raw.get("vocabulary_core", []),
        "dialogue_roles": raw.get("dialogue_roles", []),
    }


def build_mode_style_block(mode: str) -> str:
    if mode == "cinematic":
        return """
MODE: CINEMATIC
- Use present-tense, visual language and atmosphere.
- Include dialogue moments with clear speaker turns.
- Show action beats and sensory details (sound/light/movement).
- Keep the language level-appropriate; clarity has priority over poetry.
""".strip()

    if mode == "story":
        return """
MODE: STORY
- Build a short narrative arc (setup -> challenge -> outcome).
- Include emotional motivation and interpersonal context.
- Keep paragraph flow natural, with mixed sentence rhythm.
- Keep vocabulary useful for language learners at the target level.
""".strip()

    return """
MODE: STRICT
- Prioritize pedagogical clarity over creativity.
- Use short, direct sentences and explicit practical vocabulary.
- Focus on one concrete communicative objective in the scene.
- Avoid figurative language unless very common at this CEFR level.
""".strip()


def build_lesson_context(
    rag_results: list[dict[str, Any]],
    scene_data: dict[str, Any],
    target_lang: Any,
    native_lang: Any,
    mode: str,
) -> str:
    texts = [
        item["text"]
        for item in rag_results
        if isinstance(item, dict) and "text" in item
    ]

    style_block = build_mode_style_block(mode)
    texts.append(
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
Scene ID: {scene_data["scene_id"]}
Display name: {scene_data["display_name"]}
Location: {scene_data["location"]}
Goal: {scene_data["learning_goal"]}
Grammar: {", ".join(scene_data["grammar_targets"])}
Vocabulary: {", ".join(scene_data["vocabulary_core"])}
Dialogue roles: {", ".join(scene_data["dialogue_roles"])}
"""
    )

    return "\n\n".join(texts)
