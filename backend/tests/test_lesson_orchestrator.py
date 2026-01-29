from app.modules.lessons.lesson_orchestrator import generate_lesson_full


def test_generate_lesson_full(monkeypatch):
    # ---------- mocks ----------

    def mock_search_rag(title_id, k=5):
        return [
            {
                "id": "secret_agent",
                "text": "WORLD: secret agent context"
            }
        ]

    def mock_load_scene(scene_id):
        return {
            "scene_id": scene_id,
            "location": "restaurant",
            "learning_goal": "ordering food",
            "grammar_targets": ["can", "would like"],
            "vocabulary_core": ["menu", "water"],
            "dialogue_roles": ["customer", "waiter"],
        }

    def mock_generate_lesson(level, context):
        assert "WORLD:" in context
        assert "SCENE:" in context

        return {
            "level": level,
            "story": "test story",
            "vocabulary": [
                {"word": "menu", "meaning": "list of food"}
            ],
            "questions": ["What do you order?"],
            "writing_task": "Write your order."
        }

    # ---------- patch ----------

    monkeypatch.setattr(
        "app.modules.lessons.lesson_orchestrator.search_rag",
        mock_search_rag,
    )

    monkeypatch.setattr(
        "app.modules.lessons.lesson_orchestrator.load_scene",
        mock_load_scene,
    )

    monkeypatch.setattr(
        "app.modules.lessons.lesson_orchestrator.generate_lesson",
        mock_generate_lesson,
    )

    # ---------- run ----------

    result = generate_lesson_full(
        title_id="secret_agent",
        level="A1",
        scene_id="restaurant_basic",
    )

    # ---------- asserts ----------

    assert result["level"] == "A1"
    assert result["scene_id"] == "restaurant_basic"
    assert "lesson" in result

    lesson = result["lesson"]

    assert lesson["story"] == "test story"
    assert len(lesson["vocabulary"]) == 1
    assert lesson["questions"][0] == "What do you order?"
