from app.modules.lessons.lesson_orchestrator import generate_lesson_full


def test_cache_hit_skips_generation(monkeypatch):
    calls = {
        "search_rag": 0,
        "load_scene": 0,
        "generate_lesson": 0,
    }

    cached_result = {
        "level": "A1",
        "scene_id": "restaurant_basic",
        "scene": {"location": "restaurant"},
        "context_used": [],
        "lesson": {
            "level": "A1",
            "story": "cached story",
            "vocabulary": [],
            "questions": [],
            "writing_task": "cached task",
        },
    }

    class FakeCache:
        def get(self, key: str):
            return cached_result

        def set(self, key: str, value: dict) -> None:
            raise AssertionError("cache.set must not be called on cache hit")

    def fake_get_cache():
        return FakeCache()

    def fake_search_rag(*args, **kwargs):
        calls["search_rag"] += 1
        raise AssertionError("search_rag must not be called on cache hit")

    def fake_load_scene(*args, **kwargs):
        calls["load_scene"] += 1
        raise AssertionError("load_scene must not be called on cache hit")

    def fake_generate_lesson(*args, **kwargs):
        calls["generate_lesson"] += 1
        raise AssertionError("generate_lesson must not be called on cache hit")

    monkeypatch.setattr(
        "app.modules.lessons.lesson_orchestrator.get_cache",
        fake_get_cache,
    )
    monkeypatch.setattr(
        "app.modules.lessons.lesson_orchestrator.search_rag",
        fake_search_rag,
    )
    monkeypatch.setattr(
        "app.modules.lessons.lesson_orchestrator.load_scene",
        fake_load_scene,
    )
    monkeypatch.setattr(
        "app.modules.lessons.lesson_orchestrator.generate_lesson",
        fake_generate_lesson,
    )

    result = generate_lesson_full(
        title_id="secret_agent",
        level="A1",
        scene_id="restaurant_basic",
    )

    assert result == cached_result
    assert calls == {"search_rag": 0, "load_scene": 0, "generate_lesson": 0}
