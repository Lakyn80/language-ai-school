import json
import httpx

from app.core.config import settings
from app.modules.lessons.schema import LessonResponse


def generate_lesson(level: str, context: str) -> dict:
    if not settings.deepseek_api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not configured")

    system_prompt = f"""
You are an AI language teacher.

STRICT RULES:
- Use ONLY provided context
- Do NOT reference real books, movies or authors
- Do NOT invent worlds
- CEFR level: {level}

You MUST return ONLY valid JSON.

The JSON schema is EXACTLY:

{{
  "level": "{level}",
  "story": "string",
  "vocabulary": [
    {{ "word": "string", "meaning": "string" }}
  ],
  "questions": ["string"],
  "writing_task": "string"
}}

ABSOLUTE RULES:
- NO markdown
- NO explanations
- NO comments
- NO text outside JSON
"""

    payload = {
        "model": settings.deepseek_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context},
        ],
        "temperature": 0.3,
        "response_format": {
            "type": "json_object"
        }
    }

    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }

    response = httpx.post(
        f"{settings.deepseek_base_url}/chat/completions",
        headers=headers,
        json=payload,
        timeout=120,
    )

    raw_json = response.json()["choices"][0]["message"]["content"]

    try:
        data = json.loads(raw_json)
        lesson = LessonResponse(**data)
        return lesson.model_dump()

    except Exception:
        # ✅ fallback required by tests
        return {
            "level": level,
            "story": raw_json,
            "vocabulary": [],
            "questions": [],
            "writing_task": "Rewrite the story in your own words.",
        }
