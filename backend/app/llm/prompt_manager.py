from __future__ import annotations

from threading import Lock
from typing import Any, Mapping

from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate


class PromptTemplateNotFoundError(KeyError):
    pass


class PromptManager:
    def __init__(self, templates: Mapping[str, ChatPromptTemplate] | None = None):
        self._templates: dict[str, ChatPromptTemplate] = dict(templates or {})
        self._lock = Lock()

    def register(self, name: str, template: ChatPromptTemplate) -> None:
        with self._lock:
            self._templates[name] = template

    def register_from_strings(
        self,
        *,
        name: str,
        system_template: str,
        user_template: str,
    ) -> ChatPromptTemplate:
        template = ChatPromptTemplate.from_messages(
            [
                ("system", system_template),
                ("human", user_template),
            ]
        )
        self.register(name, template)
        return template

    def get(self, name: str) -> ChatPromptTemplate:
        template = self._templates.get(name)
        if template is None:
            raise PromptTemplateNotFoundError(f"Prompt template '{name}' is not registered")
        return template

    def format_messages(self, name: str, variables: Mapping[str, Any]) -> list[BaseMessage]:
        prompt = self.get(name)
        prompt_value = prompt.invoke(dict(variables))
        return list(prompt_value.to_messages())

    def has(self, name: str) -> bool:
        return name in self._templates

    @property
    def template_names(self) -> tuple[str, ...]:
        return tuple(self._templates.keys())

