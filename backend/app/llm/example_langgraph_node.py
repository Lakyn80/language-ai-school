from __future__ import annotations

from typing import Any, TypedDict

from pydantic import BaseModel, Field

from .prompt_manager import PromptManager
from .provider_router import ProviderRouter
from .retriever_factory import RetrieverFactory
from .structured_output import StructuredOutputExecutor


class LessonPlanSchema(BaseModel):
    story: str = Field(..., min_length=1)
    vocabulary: list[dict[str, str]]
    questions: list[str]
    writing_task: str = Field(..., min_length=1)


class LessonNodeState(TypedDict, total=False):
    query: str
    target_level: str
    retrieved_docs: list[dict[str, Any]]
    lesson_plan: dict[str, Any]


def build_lesson_generation_node(
    *,
    provider_router: ProviderRouter,
    retriever_factory: RetrieverFactory,
    prompt_manager: PromptManager,
    provider_name: str = "deepseek",
    model: str = "deepseek-chat",
    retriever_name: str = "faiss",
    top_k: int = 5,
):
    if not prompt_manager.has("lesson_generation"):
        prompt_manager.register_from_strings(
            name="lesson_generation",
            system_template=(
                "You are a language tutor.\n"
                "Use the retrieved context only.\n"
                "{format_instructions}"
            ),
            user_template=(
                "Level: {target_level}\n"
                "Query: {query}\n"
                "Context:\n{context}\n"
                "Return one lesson plan."
            ),
        )

    retriever = retriever_factory.create(retriever_name, default_k=top_k)
    structured = StructuredOutputExecutor(provider_router)
    prompt_template = prompt_manager.get("lesson_generation")

    def _node(state: LessonNodeState) -> LessonNodeState:
        query = state["query"]
        target_level = state.get("target_level", "A1")

        docs = retriever.invoke(query)
        context = "\n\n".join(doc.page_content for doc in docs)

        lesson_plan = structured.invoke(
            schema=LessonPlanSchema,
            prompt_template=prompt_template,
            prompt_variables={
                "query": query,
                "target_level": target_level,
                "context": context,
            },
            provider_name=provider_name,
            model=model,
            temperature=0.2,
        )

        return {
            "retrieved_docs": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                }
                for doc in docs
            ],
            "lesson_plan": lesson_plan.model_dump(),
        }

    return _node

