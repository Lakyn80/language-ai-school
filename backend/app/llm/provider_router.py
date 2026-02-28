from __future__ import annotations

import json
from threading import Lock
from typing import Any, Mapping

import httpx
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from app.core.config import settings

from .base_llm import BaseLLM, LLMRequest, LLMResponse


class ProviderRouterError(RuntimeError):
    pass


class ProviderNotRegisteredError(ProviderRouterError):
    pass


class DeepSeekChatLLM(BaseLLM):
    provider_name = "deepseek"

    def __init__(
        self,
        api_key: str,
        base_url: str,
        default_model: str,
        timeout_seconds: float = 120.0,
        http_client: httpx.Client | None = None,
    ):
        if not api_key:
            raise ValueError("DeepSeek API key must be provided")

        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._default_model = default_model
        self._timeout_seconds = timeout_seconds
        self._http_client = http_client or httpx.Client(timeout=timeout_seconds)
        self._owns_client = http_client is None

    def close(self) -> None:
        if self._owns_client:
            self._http_client.close()

    def invoke(self, request: LLMRequest) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": request.model or self._default_model,
            "messages": [self._to_openai_message(message) for message in request.messages],
            "temperature": request.temperature,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if request.response_format is not None:
            payload["response_format"] = dict(request.response_format)
        if request.tools:
            payload["tools"] = list(request.tools)

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        response = self._http_client.post(
            f"{self._base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=self._timeout_seconds,
        )

        response_payload = self._safe_json(response)
        if response.status_code >= 400:
            error = response_payload.get("error", response_payload)
            raise ProviderRouterError(
                f"DeepSeek API error ({response.status_code}): {error}"
            )

        choices = response_payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ProviderRouterError("DeepSeek response does not contain choices")

        first_choice = choices[0] if isinstance(choices[0], dict) else {}
        message_obj = first_choice.get("message", {}) if isinstance(first_choice, dict) else {}
        content = message_obj.get("content", "")
        if isinstance(content, list):
            content = json.dumps(content, ensure_ascii=False)
        if not isinstance(content, str):
            content = str(content)

        additional_kwargs: dict[str, Any] = {}
        tool_calls = message_obj.get("tool_calls")
        if isinstance(tool_calls, list):
            additional_kwargs["tool_calls"] = tool_calls

        ai_message = AIMessage(
            content=content,
            additional_kwargs=additional_kwargs,
        )

        return LLMResponse(
            provider=self.provider_name,
            model=str(payload["model"]),
            message=ai_message,
            raw=response_payload,
        )

    @staticmethod
    def _to_openai_message(message: BaseMessage) -> dict[str, Any]:
        if isinstance(message, SystemMessage):
            return {"role": "system", "content": message.content}
        if isinstance(message, HumanMessage):
            return {"role": "user", "content": message.content}
        if isinstance(message, ToolMessage):
            return {
                "role": "tool",
                "content": message.content,
                "tool_call_id": getattr(message, "tool_call_id", None),
            }
        if isinstance(message, AIMessage):
            payload: dict[str, Any] = {
                "role": "assistant",
                "content": message.content,
            }
            tool_calls = message.additional_kwargs.get("tool_calls")
            if isinstance(tool_calls, list):
                payload["tool_calls"] = tool_calls
            return payload

        role = message.type if hasattr(message, "type") else "user"
        return {"role": role, "content": str(message.content)}

    @staticmethod
    def _safe_json(response: httpx.Response) -> dict[str, Any]:
        try:
            parsed = response.json()
        except ValueError as exc:
            raise ProviderRouterError("Provider returned non-JSON response") from exc
        if not isinstance(parsed, dict):
            raise ProviderRouterError("Provider response must be a JSON object")
        return parsed


class ProviderRouter:
    def __init__(
        self,
        providers: Mapping[str, BaseLLM] | None = None,
        default_provider: str | None = None,
    ):
        self._providers: dict[str, BaseLLM] = dict(providers or {})
        self._default_provider = default_provider
        self._lock = Lock()

        if self._default_provider and self._default_provider not in self._providers:
            raise ProviderNotRegisteredError(
                f"Default provider '{self._default_provider}' is not registered"
            )

    def register(self, provider_name: str, provider: BaseLLM) -> None:
        with self._lock:
            self._providers[provider_name] = provider
            if self._default_provider is None:
                self._default_provider = provider_name

    def get_provider(self, provider_name: str | None = None) -> BaseLLM:
        effective_provider = provider_name or self._default_provider
        if not effective_provider:
            raise ProviderNotRegisteredError("No provider selected and no default provider set")
        provider = self._providers.get(effective_provider)
        if provider is None:
            raise ProviderNotRegisteredError(
                f"Provider '{effective_provider}' is not registered"
            )
        return provider

    def invoke(self, request: LLMRequest, provider_name: str | None = None) -> LLMResponse:
        provider = self.get_provider(provider_name)
        return provider.invoke(request)

    @property
    def available_providers(self) -> tuple[str, ...]:
        return tuple(self._providers.keys())


def build_default_provider_router() -> ProviderRouter:
    if not settings.deepseek_api_key:
        raise ProviderRouterError("DEEPSEEK_API_KEY is not configured")

    deepseek = DeepSeekChatLLM(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        default_model=settings.deepseek_model,
    )
    return ProviderRouter(
        providers={"deepseek": deepseek},
        default_provider="deepseek",
    )

