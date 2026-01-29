from app.modules.lessons.cache.lesson_cache import get_cache


def test_lesson_cache_interface():
    cache = get_cache()

    assert cache.get("missing") is None

    lesson = {
        "level": "A1",
        "story": "test",
        "vocabulary": [],
        "questions": [],
        "writing_task": "task",
    }

    cache.set("lesson:A1:restaurant", lesson)

    cached = cache.get("lesson:A1:restaurant")

    assert cached == lesson
