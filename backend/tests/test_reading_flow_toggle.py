from app.core.config import settings
from app.modules.reading.flow import run_reading_flow
from app.modules.reading.schemas import ReadingEvaluateRequest, ReadingEvaluateResponse
from app.modules.reading.workflows.langgraph_flow import run_langgraph_reading_flow


def _payload() -> ReadingEvaluateRequest:
    return ReadingEvaluateRequest(
        level="A1",
        target_language="en",
        native_language="cs",
        text="John is at school.",
        student_summary="John is at school.",
    )


def _response(score: int = 100) -> ReadingEvaluateResponse:
    return ReadingEvaluateResponse(
        score=score,
        result="PASS",
        feedback_native="ok",
        missing=[],
        hallucinations=[],
    )


def test_run_reading_flow_uses_legacy_when_flag_disabled(monkeypatch):
    monkeypatch.setattr(settings, "use_langgraph_reading", False)
    monkeypatch.setattr(
        "app.modules.reading.flow.run_legacy_reading_flow",
        lambda payload: _response(91),
    )
    monkeypatch.setattr(
        "app.modules.reading.flow.run_langgraph_reading_flow",
        lambda payload: _response(33),
    )

    result = run_reading_flow(_payload())

    assert result.score == 91


def test_run_reading_flow_uses_langgraph_when_flag_enabled(monkeypatch):
    monkeypatch.setattr(settings, "use_langgraph_reading", True)
    monkeypatch.setattr(
        "app.modules.reading.flow.run_legacy_reading_flow",
        lambda payload: _response(11),
    )
    monkeypatch.setattr(
        "app.modules.reading.flow.run_langgraph_reading_flow",
        lambda payload: _response(88),
    )

    result = run_reading_flow(_payload())

    assert result.score == 88


def test_langgraph_flow_falls_back_to_legacy_when_graph_unavailable(monkeypatch):
    monkeypatch.setattr(
        "app.modules.reading.workflows.langgraph_flow._get_graph",
        lambda: None,
    )
    monkeypatch.setattr(
        "app.modules.reading.workflows.legacy.run_legacy_reading_flow",
        lambda payload: _response(77),
    )

    result = run_langgraph_reading_flow(_payload())

    assert result.score == 77
