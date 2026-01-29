import json
import httpx
from app.core.config import settings


def generate_lesson(level: str, context: str) -> dict:
    """
    DeepSeek LLM lesson generator.
    Uses ONLY RAG context.
    """

    if not settings.deepseek_api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not configured")

    system_prompt = f"""
You are an AI language teacher.

STRICT RULES:
- Use ONLY the provided context.
- Do NOT add external knowledge.
- Do NOT reference real books, movies, authors.
- Generate completely original educational content.
- Follow CEFR level strictly: {level}

CEFR RULES:

A1:
- very short sentences
- present simple only
- basic vocabulary
- max 600 words

A2:
- present + past simple
- simple connectors (and, but, because)
- max 800 words

B1:
- present, past, future
- longer sentences
- simple dialogues
- max 1000 words

B2:
- complex grammar
- opinions and emotions
- rich vocabulary
- max 1200 words

Return VALID JSON ONLY:

{
  "level": "...",
  "story": "...",
  "vocabulary": [
    { "word": "", "meaning": "" }
  ],
  "questions": [
    "..."
  ],
  "writing_task": "..."
}
"""

    payload = {
        "model": settings.deepseek_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context},
        ],
        "temperature": 0.7,
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

    data = response.json()

    content = data["choices"][0]["message"]["content"]

    try:
        return json.loads(content)
    except Exception:
        return {
            "level": level,
            "error": "Invalid JSON returned by DeepSeek",
            "raw_output": content,
        }
