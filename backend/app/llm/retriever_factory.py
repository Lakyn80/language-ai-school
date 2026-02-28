from __future__ import annotations

import asyncio
from threading import Lock
from typing import Any, Callable, Mapping, Sequence

from langchain_core.callbacks import (
    AsyncCallbackManagerForRetrieverRun,
    CallbackManagerForRetrieverRun,
)
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever


class FaissRetrieverAdapter(BaseRetriever):
    search_fn: Callable[[str, int], Sequence[dict[str, Any]]]
    default_k: int = 5

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:
        rows = self.search_fn(query, self.default_k)
        documents: list[Document] = []
        for row in rows:
            text = str(row.get("text", ""))
            metadata = {key: value for key, value in row.items() if key != "text"}
            documents.append(
                Document(
                    page_content=text,
                    metadata=metadata,
                )
            )
        return documents

    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: AsyncCallbackManagerForRetrieverRun,
    ) -> list[Document]:
        return await asyncio.to_thread(self._get_relevant_documents, query, run_manager=run_manager)


class RetrieverFactory:
    def __init__(self):
        self._builders: dict[str, Callable[..., BaseRetriever]] = {}
        self._lock = Lock()

    def register(self, retriever_name: str, builder: Callable[..., BaseRetriever]) -> None:
        with self._lock:
            self._builders[retriever_name] = builder

    def create(self, retriever_name: str, **kwargs: Any) -> BaseRetriever:
        builder = self._builders.get(retriever_name)
        if builder is None:
            available = ", ".join(sorted(self._builders.keys())) or "<none>"
            raise ValueError(
                f"Retriever '{retriever_name}' is not registered. Available: {available}"
            )
        return builder(**kwargs)

    @property
    def available_retrievers(self) -> tuple[str, ...]:
        return tuple(self._builders.keys())


def build_default_retriever_factory(
    search_fn: Callable[[str, int], Sequence[dict[str, Any]]] | None = None,
) -> RetrieverFactory:
    if search_fn is None:
        from app.modules.rag.service import search_rag as default_search_rag

        search_fn = default_search_rag

    factory = RetrieverFactory()
    factory.register(
        "faiss",
        lambda default_k=5: FaissRetrieverAdapter(
            search_fn=search_fn,
            default_k=default_k,
        ),
    )
    return factory

