from __future__ import annotations

import json
from typing import Any, Mapping, TypeVar

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from .base_llm import LLMRequest
from .provider_router import ProviderRouter

TModel = TypeVar("TModel", bound=BaseModel)


class StructuredOutputError(RuntimeError):
    pass


class StructuredOutputExecutor:
    def __init__(self, provider_router: ProviderRouter):
        self._provider_router = provider_router

    def invoke(
        self,
        *,
        schema: type[TModel],
        prompt_template: ChatPromptTemplate,
        prompt_variables: Mapping[str, Any],
        model: str,
        provider_name: str | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> TModel:
        parser = PydanticOutputParser(pydantic_object=schema)
        variables = dict(prompt_variables)
        variables.setdefault("format_instructions", parser.get_format_instructions())

        prompt_value = prompt_template.invoke(variables)
        request = LLMRequest(
            model=model,
            messages=prompt_value.to_messages(),
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )

        response = self._provider_router.invoke(
            request=request,
            provider_name=provider_name,
        )

        raw_content = response.message.content
        content = self._normalize_text(raw_content)

        try:
            return parser.parse(content)
        except Exception as exc:
            raise StructuredOutputError(
                f"Structured output parse failed for schema '{schema.__name__}'"
            ) from exc

    @staticmethod
    def _normalize_text(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, (dict, list)):
            return json.dumps(content, ensure_ascii=False)
        return str(content)

