from app.modules.adaptive.schemas import AdaptiveLessonRequest
from app.modules.adaptive.service import run_adaptive_lesson
from app.modules.adaptive.state_store import FileHistoryStore, FileStateStore
from app.modules.reading import ReadingEvaluateResponse


def _payload(run_id: str | None = None) -> AdaptiveLessonRequest:
    return AdaptiveLessonRequest(
        student_id="student-1",
        title_id="secret_agent",
        scene_id="restaurant_basic",
        level="A1",
        mode="strict",
        target_language="en",
        native_language="cs",
        text="John went to the airport.",
        student_summary="John went to the airport.",
        run_id=run_id,
    )


def test_adaptive_flow_fail_branch(monkeypatch, tmp_path):
    from app.modules.adaptive.workflows import langgraph_flow as flow_module

    monkeypatch.setattr(flow_module, "_GRAPH", None)
    monkeypatch.setattr(flow_module, "_STATE_STORE", FileStateStore(tmp_path / "runs"))
    monkeypatch.setattr(flow_module, "_HISTORY_STORE", FileHistoryStore(tmp_path / "history"))
    monkeypatch.setattr(
        flow_module,
        "evaluate_reading_summary",
        lambda payload: ReadingEvaluateResponse(
            score=22,
            result="FAIL",
            feedback_native="x",
            missing=["Fact A"],
            hallucinations=["Fact B"],
        ),
    )
    monkeypatch.setattr(
        flow_module,
        "search_rag",
        lambda title_id, k=5: [{"id": "secret_agent", "text": "ctx"}],
    )
    monkeypatch.setattr(
        flow_module,
        "get_scene_by_slug",
        lambda slug: {
            "scene_id": slug,
            "display_name": "Restaurant",
            "location": "restaurant",
            "learning_goal": "order food",
            "grammar_targets": ["can"],
            "vocabulary_core": ["menu"],
            "dialogue_roles": ["customer", "waiter"],
        },
    )
    monkeypatch.setattr(
        flow_module,
        "generate_adaptive_lesson",
        lambda **kwargs: {
            "lesson": {
                "level": "A1",
                "story": "Simple story.",
                "vocabulary": [{"word": "menu", "meaning": "menu"}],
                "questions": ["Q1"],
                "writing_task": "Write three sentences.",
                "drill": ["Retell correctly: Fact A"],
            },
            "provider": "mock",
            "model": "mock",
            "attempts": [],
        },
    )

    result = run_adaptive_lesson(_payload())

    assert result.branch == "FAIL"
    assert result.lesson.drill == ["Retell correctly: Fact A"]
    assert result.generation_meta["provider"] == "mock"
    assert "finalize" in result.checkpoints


def test_adaptive_flow_resume(monkeypatch, tmp_path):
    from app.modules.adaptive.workflows import langgraph_flow as flow_module

    monkeypatch.setattr(flow_module, "_GRAPH", None)
    monkeypatch.setattr(flow_module, "_STATE_STORE", FileStateStore(tmp_path / "runs"))
    monkeypatch.setattr(flow_module, "_HISTORY_STORE", FileHistoryStore(tmp_path / "history"))
    monkeypatch.setattr(
        flow_module,
        "evaluate_reading_summary",
        lambda payload: ReadingEvaluateResponse(
            score=90,
            result="PASS",
            feedback_native="x",
            missing=[],
            hallucinations=[],
        ),
    )
    monkeypatch.setattr(
        flow_module,
        "search_rag",
        lambda title_id, k=5: [{"id": "secret_agent", "text": "ctx"}],
    )
    monkeypatch.setattr(
        flow_module,
        "get_scene_by_slug",
        lambda slug: {
            "scene_id": slug,
            "display_name": "Restaurant",
            "location": "restaurant",
            "learning_goal": "order food",
            "grammar_targets": ["can"],
            "vocabulary_core": ["menu"],
            "dialogue_roles": ["customer", "waiter"],
        },
    )

    call_counter = {"count": 0}

    def _mock_generator(**kwargs):
        call_counter["count"] += 1
        return {
            "lesson": {
                "level": "A1",
                "story": "Harder continuation.",
                "vocabulary": [{"word": "menu", "meaning": "menu"}],
                "questions": ["Q1"],
                "writing_task": "Write six sentences.",
                "drill": [],
            },
            "provider": "mock",
            "model": "mock",
            "attempts": [],
        }

    monkeypatch.setattr(flow_module, "generate_adaptive_lesson", _mock_generator)

    first_result = run_adaptive_lesson(_payload())
    assert call_counter["count"] == 1

    second_result = run_adaptive_lesson(_payload(run_id=first_result.run_id))

    assert second_result.run_id == first_result.run_id
    assert second_result.resumed is True
    assert call_counter["count"] == 1
