from threading import Lock
from typing import Any, TypedDict

from app.pedagogy.cefr.scoring import evaluate_cefr_similarity
from app.pedagogy.comprehension.evaluator import semantic_similarity
from app.pedagogy.comprehension.feedback import extract_missing_and_hallucinations
from app.pedagogy.comprehension.feedback_text import build_feedback_text
from app.pedagogy.comprehension.translation import translate_to_target_cached

from ..schemas import ReadingEvaluateRequest, ReadingEvaluateResponse


class ReadingFlowState(TypedDict, total=False):
    payload: ReadingEvaluateRequest
    translated_summary: str
    similarity: float
    missing: list[str]
    hallucinations: list[str]
    final_similarity: float
    score: int
    result: str
    feedback_native: str
    response: ReadingEvaluateResponse


_GRAPH = None
_GRAPH_LOCK = Lock()


def _step_translate(state: ReadingFlowState) -> ReadingFlowState:
    payload = state["payload"]
    translated_summary = translate_to_target_cached(
        payload.student_summary,
        payload.native_language,
        payload.target_language,
    )
    return {"translated_summary": translated_summary}


def _step_similarity(state: ReadingFlowState) -> ReadingFlowState:
    payload = state["payload"]
    translated_summary = state["translated_summary"]

    similarity = semantic_similarity(payload.text, translated_summary)
    return {"similarity": similarity}


def _step_coverage(state: ReadingFlowState) -> ReadingFlowState:
    payload = state["payload"]
    translated_summary = state["translated_summary"]

    missing, hallucinations = extract_missing_and_hallucinations(
        original_text=payload.text,
        student_text=translated_summary,
    )

    total_sentences = max(payload.text.count("."), 1)
    covered = total_sentences - len(missing)
    coverage_ratio = max(covered / total_sentences, 0.0)

    final_similarity = state["similarity"] * coverage_ratio
    return {
        "missing": missing,
        "hallucinations": hallucinations,
        "final_similarity": final_similarity,
    }


def _step_cefr(state: ReadingFlowState) -> ReadingFlowState:
    payload = state["payload"]
    score, result = evaluate_cefr_similarity(
        payload.level,
        state["final_similarity"],
    )
    return {
        "score": score,
        "result": result,
    }


def _step_feedback(state: ReadingFlowState) -> ReadingFlowState:
    payload = state["payload"]
    feedback_native = build_feedback_text(
        native_language=payload.native_language,
        result=state["result"],
        missing=state["missing"],
        hallucinations=state["hallucinations"],
    )
    return {"feedback_native": feedback_native}


def _step_finalize(state: ReadingFlowState) -> ReadingFlowState:
    response = ReadingEvaluateResponse(
        score=int(state["final_similarity"] * 100),
        result=state["result"],
        feedback_native=state["feedback_native"],
        missing=state["missing"],
        hallucinations=state["hallucinations"],
    )
    return {"response": response}


def _build_graph():
    try:
        from langgraph.graph import END, StateGraph
    except Exception:
        return None

    workflow = StateGraph(ReadingFlowState)

    workflow.add_node("translate", _step_translate)
    workflow.add_node("similarity", _step_similarity)
    workflow.add_node("coverage", _step_coverage)
    workflow.add_node("cefr", _step_cefr)
    workflow.add_node("feedback", _step_feedback)
    workflow.add_node("finalize", _step_finalize)

    workflow.set_entry_point("translate")
    workflow.add_edge("translate", "similarity")
    workflow.add_edge("similarity", "coverage")
    workflow.add_edge("coverage", "cefr")
    workflow.add_edge("cefr", "feedback")
    workflow.add_edge("feedback", "finalize")
    workflow.add_edge("finalize", END)

    return workflow.compile()


def _get_graph():
    global _GRAPH
    if _GRAPH is not None:
        return _GRAPH

    with _GRAPH_LOCK:
        if _GRAPH is None:
            _GRAPH = _build_graph()
    return _GRAPH


def run_langgraph_reading_flow(
    payload: ReadingEvaluateRequest,
) -> ReadingEvaluateResponse:
    graph = _get_graph()
    if graph is None:
        from .legacy import run_legacy_reading_flow

        return run_legacy_reading_flow(payload)

    final_state: dict[str, Any] = graph.invoke({"payload": payload})
    response = final_state.get("response")
    if isinstance(response, ReadingEvaluateResponse):
        return response

    from .legacy import run_legacy_reading_flow

    return run_legacy_reading_flow(payload)


def _serialize_debug_value(value: Any) -> Any:
    if isinstance(value, ReadingEvaluateRequest):
        return value.model_dump()
    if isinstance(value, ReadingEvaluateResponse):
        return value.model_dump()
    return value


def _serialize_debug_state(state: dict[str, Any]) -> dict[str, Any]:
    return {key: _serialize_debug_value(value) for key, value in state.items()}


def run_langgraph_reading_flow_debug(
    payload: ReadingEvaluateRequest,
) -> dict[str, Any]:
    graph = _get_graph()
    if graph is None:
        from .legacy import run_legacy_reading_flow

        fallback_response = run_legacy_reading_flow(payload)
        return {
            "engine": "legacy_fallback",
            "reason": "langgraph_unavailable",
            "steps": [
                {
                    "node": "legacy",
                    "state": {"response": fallback_response.model_dump()},
                }
            ],
            "response": fallback_response.model_dump(),
        }

    state: dict[str, Any] = {"payload": payload}
    steps: list[dict[str, Any]] = []
    graph_steps = [
        ("translate", _step_translate),
        ("similarity", _step_similarity),
        ("coverage", _step_coverage),
        ("cefr", _step_cefr),
        ("feedback", _step_feedback),
        ("finalize", _step_finalize),
    ]

    for node_name, step_fn in graph_steps:
        update = step_fn(state)
        state.update(update)
        steps.append(
            {
                "node": node_name,
                "update": _serialize_debug_state(update),
                "state": _serialize_debug_state(state),
            }
        )

    response = state.get("response")
    if not isinstance(response, ReadingEvaluateResponse):
        from .legacy import run_legacy_reading_flow

        fallback_response = run_legacy_reading_flow(payload)
        return {
            "engine": "legacy_fallback",
            "reason": "debug_response_missing",
            "steps": steps,
            "response": fallback_response.model_dump(),
        }

    return {
        "engine": "langgraph",
        "steps": steps,
        "response": response.model_dump(),
    }
