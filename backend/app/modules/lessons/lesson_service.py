import json
import re
import httpx

from app.core.config import settings
from app.modules.lessons.schema import LessonResponse


def extract_json(text: str) -> dict:
    text = text.strip()

    if text.startswith("`"):
        text = re.sub(r"^`json", "", text)
        text = re.sub(r"^`", "", text)
        text = re.sub(r"`$", "", text)

    return json.loads(text)


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

Return VALID JSON ONLY:

{{
  "level": "{level}",
  "story": "",
  "vocabulary": [
    {{ "word": "", "meaning": "" }}
  ],
  "questions": [],
  "writing_task": ""
}}

NO markdown.
NO explanations.
"""

    payload = {
        "model": settings.deepseek_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context},
        ],
        "temperature": 0.4,
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

    raw = response.json()["choices"][0]["message"]["content"]

    try:
        data = extract_json(raw)
    except Exception:
        return {
            "level": level,
            "story": raw,
            "vocabulary": [],
            "questions": [],
            "writing_task": "Rewrite the story in your own words.",
        }

    lesson = LessonResponse(**data)
    return lesson.model_dump()
