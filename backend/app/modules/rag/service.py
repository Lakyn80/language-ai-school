from typing import Any, List

from app.core.config import settings

from .vectorstore import VectorStore

Document = dict[str, Any]
_STORE: VectorStore | None = None


def deduplicate_results(results: List[Document]) -> List[Document]:
    deduplicated: list[Document] = []
    seen_ids: set[str] = set()
    seen_texts: set[str] = set()

    for item in results:
        if not isinstance(item, dict):
            continue

        doc_id = str(item.get("id", "")).strip()
        text = str(item.get("text", "")).strip()

        if not doc_id:
            continue
        if doc_id in seen_ids:
            continue
        if text and text in seen_texts:
            continue

        seen_ids.add(doc_id)
        if text:
            seen_texts.add(text)
        deduplicated.append(item)

    return deduplicated


def get_store() -> VectorStore:
    global _STORE
    if _STORE is None:
        _STORE = VectorStore(
            index_path=settings.rag_index_path,
            model_name=settings.rag_embedding_model,
        )
    return _STORE


def initialize_rag() -> None:
    get_store().preload()


def search_rag(query: str, k: int = 5) -> List[Document]:
    store = get_store()
    results = store.search(query, top_k=k)
    return deduplicate_results(results)
