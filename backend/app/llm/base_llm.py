from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from langchain_core.messages import AIMessage, BaseMessage


@dataclass(frozen=True)
class LLMRequest:
    model: str
    messages: Sequence[BaseMessage]
    temperature: float = 0.0
    max_tokens: int | None = None
    response_format: Mapping[str, Any] | None = None
    tools: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LLMResponse:
    provider: str
    model: str
    message: AIMessage
    raw: Mapping[str, Any]


class BaseLLM(ABC):
    provider_name: str

    @abstractmethod
    def invoke(self, request: LLMRequest) -> LLMResponse:
        raise NotImplementedError

