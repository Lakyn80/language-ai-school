from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Any, TypedDict
from uuid import uuid4

from pydantic import BaseModel

from app.modules.rag import search_rag
from app.modules.reading import (
    ReadingEvaluateRequest,
    ReadingEvaluateResponse,
    evaluate_reading_summary,
)
from app.modules.scenes import get_scene_by_slug
from app.pedagogy.cefr.levels import CEFRLevel
from app.pedagogy.cefr.rules import CEFR_RULES

from ..generator import generate_adaptive_lesson
from ..schemas import (
    AdaptiveLessonPayload,
    AdaptiveLessonRequest,
    AdaptiveLessonResponse,
)
from ..state_store import FileHistoryStore, FileStateStore


class AdaptiveFlowState(TypedDict, total=False):
    payload: AdaptiveLessonRequest
    run_id: str
    resumed: bool
    reading: ReadingEvaluateResponse
    branch: str
    rag_context: list[dict[str, Any]]
    student_history: dict[str, Any]
    cefr_rules: dict[str, Any]
    scene_data: dict[str, Any]
    lesson: AdaptiveLessonPayload
    generation_meta: dict[str, Any]
    history_saved: bool
    checkpoints: list[str]
    response: AdaptiveLessonResponse


_GRAPH = None
_GRAPH_LOCK = Lock()
_STATE_STORE = FileStateStore()
_HISTORY_STORE = FileHistoryStore()


def _serialize_value(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump()
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    return value


def _serialize_state(state: dict[str, Any]) -> dict[str, Any]:
    return {key: _serialize_value(value) for key, value in state.items()}


def _with_checkpoint(
    step_name: str,
    state: AdaptiveFlowState,
    update: dict[str, Any],
) -> dict[str, Any]:
    checkpoints = list(state.get("checkpoints", []))
    checkpoints.append(step_name)

    merged_update = dict(update)
    merged_update["checkpoints"] = checkpoints

    combined_state: dict[str, Any] = dict(state)
    combined_state.update(merged_update)
    run_id = combined_state.get("run_id")
    if isinstance(run_id, str) and run_id:
        _STATE_STORE.save_state(run_id, _serialize_state(combined_state))

    return merged_update


def _to_scene_payload(scene: dict | object | None, fallback_scene_id: str) -> dict[str, Any]:
    if scene is None:
        return {
            "scene_id": fallback_scene_id,
            "display_name": fallback_scene_id,
            "location": fallback_scene_id,
            "learning_goal": "",
            "grammar_targets": [],
            "vocabulary_core": [],
            "dialogue_roles": [],
        }

    if isinstance(scene, dict):
        data = scene
    else:
        data = {
            "scene_id": getattr(scene, "slug", fallback_scene_id),
            "display_name": getattr(scene, "title", fallback_scene_id),
            "location": getattr(scene, "slug", fallback_scene_id),
            "learning_goal": getattr(scene, "description", ""),
            "grammar_targets": [],
            "vocabulary_core": [],
            "dialogue_roles": [],
        }
    return {
        "scene_id": data.get("scene_id", fallback_scene_id),
        "display_name": data.get("display_name", fallback_scene_id),
        "location": data.get("location", fallback_scene_id),
        "learning_goal": data.get("learning_goal", ""),
        "grammar_targets": data.get("grammar_targets", []),
        "vocabulary_core": data.get("vocabulary_core", []),
        "dialogue_roles": data.get("dialogue_roles", []),
    }


def _load_cefr_rules(level: str) -> dict[str, Any]:
    cefr_level = CEFRLevel(level.upper())
    rules = CEFR_RULES[cefr_level]
    return {
        "level": cefr_level.value,
        "allowed_tenses": rules.allowed_tenses,
        "max_sentence_words": rules.max_sentence_words,
        "allow_passive": rules.allow_passive,
        "allow_conditionals": rules.allow_conditionals,
        "allow_subordinate_clauses": rules.allow_subordinate_clauses,
    }


def _safe_future_result(future, default):
    try:
        value = future.result()
        return default if value is None else value
    except Exception:
        return default


def _reading_to_dict(reading: ReadingEvaluateResponse | dict[str, Any]) -> dict[str, Any]:
    if isinstance(reading, ReadingEvaluateResponse):
        return reading.model_dump()
    if isinstance(reading, dict):
        return reading
    return {}


def _lesson_to_model(lesson: AdaptiveLessonPayload | dict[str, Any]) -> AdaptiveLessonPayload:
    if isinstance(lesson, AdaptiveLessonPayload):
        return lesson
    return AdaptiveLessonPayload(**lesson)


def _reading_to_model(reading: ReadingEvaluateResponse | dict[str, Any]) -> ReadingEvaluateResponse:
    if isinstance(reading, ReadingEvaluateResponse):
        return reading
    return ReadingEvaluateResponse(**reading)


def _step_init(state: AdaptiveFlowState) -> dict[str, Any]:
    if state.get("run_id"):
        return {}

    payload = state["payload"]
    run_id = payload.run_id or uuid4().hex
    return _with_checkpoint(
        "init",
        state,
        {
            "run_id": run_id,
            "resumed": bool(payload.run_id),
        },
    )


def _step_reading(state: AdaptiveFlowState) -> dict[str, Any]:
    if state.get("reading") is not None:
        return {}

    payload = state["payload"]
    reading_payload = ReadingEvaluateRequest(
        level=payload.level,
        target_language=payload.target_language,
        native_language=payload.native_language,
        text=payload.text,
        student_summary=payload.student_summary,
    )
    reading = evaluate_reading_summary(reading_payload)
    return _with_checkpoint("reading", state, {"reading": reading})


def _step_branch(state: AdaptiveFlowState) -> dict[str, Any]:
    if state.get("branch") is not None:
        return {}

    reading = _reading_to_model(state["reading"])
    branch = "PASS" if reading.result.upper() == "PASS" else "FAIL"
    return _with_checkpoint("branch", state, {"branch": branch})


def _step_load_context_parallel(state: AdaptiveFlowState) -> dict[str, Any]:
    has_context = (
        state.get("rag_context") is not None
        and state.get("student_history") is not None
        and state.get("cefr_rules") is not None
        and state.get("scene_data") is not None
    )
    if has_context:
        return {}

    payload = state["payload"]
    with ThreadPoolExecutor(max_workers=4) as executor:
        rag_future = executor.submit(search_rag, payload.title_id, 5)
        history_future = executor.submit(
            _HISTORY_STORE.load_student_history,
            payload.student_id,
        )
        cefr_future = executor.submit(_load_cefr_rules, payload.level)
        scene_future = executor.submit(get_scene_by_slug, payload.scene_id)

        rag_context = _safe_future_result(rag_future, [])
        student_history = _safe_future_result(history_future, {"records": []})
        cefr_rules = _safe_future_result(cefr_future, _load_cefr_rules(payload.level))
        scene = _safe_future_result(scene_future, None)

    scene_data = _to_scene_payload(scene, payload.scene_id)
    return _with_checkpoint(
        "load_context_parallel",
        state,
        {
            "rag_context": rag_context,
            "student_history": student_history,
            "cefr_rules": cefr_rules,
            "scene_data": scene_data,
        },
    )


def _step_generate_pass(state: AdaptiveFlowState) -> dict[str, Any]:
    if state.get("lesson") is not None:
        return {}

    payload = state["payload"]
    reading_result = _reading_to_dict(state["reading"])
    cache_key = (
        f"{payload.title_id}|{payload.scene_id}|{payload.level}|{payload.mode}|"
        f"{payload.target_language}|PASS"
    )
    generated = generate_adaptive_lesson(
        level=payload.level,
        branch="PASS",
        rag_context=state["rag_context"],
        scene_data=state["scene_data"],
        student_history=state["student_history"],
        cefr_rules=state["cefr_rules"],
        reading_result=reading_result,
        cache_key=cache_key,
    )
    lesson = _lesson_to_model(generated["lesson"])
    generation_meta = {
        "branch": "PASS",
        "provider": generated.get("provider"),
        "model": generated.get("model"),
        "attempts": generated.get("attempts", []),
        "monitor": generated.get("monitor", {}),
    }
    return _with_checkpoint(
        "generate_pass",
        state,
        {
            "lesson": lesson,
            "generation_meta": generation_meta,
        },
    )


def _step_generate_fail(state: AdaptiveFlowState) -> dict[str, Any]:
    if state.get("lesson") is not None:
        return {}

    payload = state["payload"]
    reading_result = _reading_to_dict(state["reading"])
    cache_key = (
        f"{payload.title_id}|{payload.scene_id}|{payload.level}|{payload.mode}|"
        f"{payload.target_language}|FAIL"
    )
    generated = generate_adaptive_lesson(
        level=payload.level,
        branch="FAIL",
        rag_context=state["rag_context"],
        scene_data=state["scene_data"],
        student_history=state["student_history"],
        cefr_rules=state["cefr_rules"],
        reading_result=reading_result,
        cache_key=cache_key,
    )
    lesson = _lesson_to_model(generated["lesson"])
    generation_meta = {
        "branch": "FAIL",
        "provider": generated.get("provider"),
        "model": generated.get("model"),
        "attempts": generated.get("attempts", []),
        "monitor": generated.get("monitor", {}),
    }
    return _with_checkpoint(
        "generate_fail",
        state,
        {
            "lesson": lesson,
            "generation_meta": generation_meta,
        },
    )


def _step_save_history(state: AdaptiveFlowState) -> dict[str, Any]:
    if state.get("history_saved"):
        return {}

    payload = state["payload"]
    reading = _reading_to_dict(state["reading"])

    _HISTORY_STORE.append_student_history(
        payload.student_id,
        {
            "run_id": state.get("run_id"),
            "level": payload.level,
            "result": reading.get("result"),
            "score": reading.get("score"),
            "missing": reading.get("missing", []),
            "hallucinations": reading.get("hallucinations", []),
        },
    )
    return _with_checkpoint("save_history", state, {"history_saved": True})


def _step_finalize(state: AdaptiveFlowState) -> dict[str, Any]:
    if state.get("response") is not None:
        return {}

    checkpoints = list(state.get("checkpoints", []))
    checkpoints.append("finalize")
    response = AdaptiveLessonResponse(
        run_id=state["run_id"],
        branch=state["branch"],
        resumed=bool(state.get("resumed", False)),
        reading=_reading_to_model(state["reading"]),
        lesson=_lesson_to_model(state["lesson"]),
        checkpoints=checkpoints,
        generation_meta=dict(state.get("generation_meta", {})),
    )
    return _with_checkpoint("finalize", state, {"response": response})


def _select_generation_node(state: AdaptiveFlowState) -> str:
    branch = str(state.get("branch", "FAIL")).upper()
    return "generate_pass" if branch == "PASS" else "generate_fail"


def _build_graph():
    try:
        from langgraph.graph import END, StateGraph
    except Exception:
        return None

    workflow = StateGraph(AdaptiveFlowState)
    workflow.add_node("init", _step_init)
    workflow.add_node("reading", _step_reading)
    workflow.add_node("branch", _step_branch)
    workflow.add_node("load_context_parallel", _step_load_context_parallel)
    workflow.add_node("generate_pass", _step_generate_pass)
    workflow.add_node("generate_fail", _step_generate_fail)
    workflow.add_node("save_history", _step_save_history)
    workflow.add_node("finalize", _step_finalize)

    workflow.set_entry_point("init")
    workflow.add_edge("init", "reading")
    workflow.add_edge("reading", "branch")
    workflow.add_edge("branch", "load_context_parallel")
    workflow.add_conditional_edges(
        "load_context_parallel",
        _select_generation_node,
        {
            "generate_pass": "generate_pass",
            "generate_fail": "generate_fail",
        },
    )
    workflow.add_edge("generate_pass", "save_history")
    workflow.add_edge("generate_fail", "save_history")
    workflow.add_edge("save_history", "finalize")
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


def _hydrate_saved_state(raw_state: dict[str, Any]) -> AdaptiveFlowState:
    hydrated: AdaptiveFlowState = dict(raw_state)

    payload = hydrated.get("payload")
    if isinstance(payload, dict):
        hydrated["payload"] = AdaptiveLessonRequest(**payload)

    reading = hydrated.get("reading")
    if isinstance(reading, dict):
        hydrated["reading"] = ReadingEvaluateResponse(**reading)

    lesson = hydrated.get("lesson")
    if isinstance(lesson, dict):
        hydrated["lesson"] = AdaptiveLessonPayload(**lesson)

    response = hydrated.get("response")
    if isinstance(response, dict):
        hydrated["response"] = AdaptiveLessonResponse(**response)

    return hydrated


def _run_without_graph(initial_state: AdaptiveFlowState) -> AdaptiveFlowState:
    state: AdaptiveFlowState = dict(initial_state)
    for step in (_step_init, _step_reading, _step_branch, _step_load_context_parallel):
        update = step(state)
        if update:
            state.update(update)

    generation_step = _step_generate_pass if state.get("branch") == "PASS" else _step_generate_fail
    generation_update = generation_step(state)
    if generation_update:
        state.update(generation_update)

    for step in (_step_save_history, _step_finalize):
        update = step(state)
        if update:
            state.update(update)
    return state


def run_adaptive_langgraph_flow(
    payload: AdaptiveLessonRequest,
) -> AdaptiveLessonResponse:
    graph = _get_graph()

    initial_state: AdaptiveFlowState = {"payload": payload}
    resumed_request = False
    if payload.run_id:
        saved_state = _STATE_STORE.load_state(payload.run_id)
        if isinstance(saved_state, dict):
            initial_state = _hydrate_saved_state(saved_state)
            initial_state["payload"] = payload
            initial_state["resumed"] = True
            resumed_request = True

    if graph is None:
        final_state = _run_without_graph(initial_state)
    else:
        final_state: dict[str, Any] = graph.invoke(initial_state)

    response = final_state.get("response")
    if isinstance(response, AdaptiveLessonResponse):
        if resumed_request:
            response.resumed = True
        return response
    if isinstance(response, dict):
        parsed = AdaptiveLessonResponse(**response)
        if resumed_request:
            parsed.resumed = True
        return parsed

    raise RuntimeError("Adaptive flow did not produce a response")
