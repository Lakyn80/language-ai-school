import json
from pathlib import Path
from typing import Any

from .vectorstore import VectorStore
from app.core.config import settings

DATA_DIR = Path("app/data/worlds")


def _stable_world_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _build_documents() -> list[dict[str, str]]:
    documents: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    seen_texts: set[str] = set()

    for file in sorted(DATA_DIR.glob("*.json")):
        with open(file, "r", encoding="utf-8") as handle:
            data = json.load(handle)

        world_id = str(data.get("world_id") or file.stem)
        text = _stable_world_text(data)

        # Stable chunk id for deterministic ingestion ordering.
        chunk_id = f"{world_id}:chunk:0000"

        if chunk_id in seen_ids:
            continue
        if text in seen_texts:
            continue

        seen_ids.add(chunk_id)
        seen_texts.add(text)

        documents.append(
            {
                "id": chunk_id,
                "world_id": world_id,
                "text": text,
            }
        )

    # Ensure metadata ordering is deterministic and consistent with embeddings.
    return sorted(documents, key=lambda item: item["id"])


def ingest_titles():
    store = VectorStore(
        index_path=settings.rag_index_path,
        model_name=settings.rag_embedding_model,
    )

    documents = _build_documents()

    store.build_index(documents)
    print(f"Ingested {len(documents)} chunks.")


if __name__ == "__main__":
    ingest_titles()
