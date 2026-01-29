from app.modules.rag.service import search_rag
from app.modules.lessons.lesson_service import generate_lesson


def generate_lesson_full(title_id: str, level: str):
    rag_results = search_rag(title_id, k=5)

    context = "\n".join(
        [str(item) for item in rag_results]
    )

    lesson_text = generate_lesson(level, context)

    return {
        "level": level,
        "context_used": rag_results,
        "lesson": lesson_text
    }
