import json
from pathlib import Path

from app.modules.rag.vectorstore import VectorStore
from app.core.config import settings

DATA_DIR = Path("app/data/worlds")


def ingest_titles():
    store = VectorStore(
        index_path=settings.rag_index_path,
        model_name=settings.rag_embedding_model,
    )

    documents = []

    for file in DATA_DIR.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        documents.append(
            {
                "id": data.get("world_id"),
                "text": json.dumps(data, ensure_ascii=False),
            }
        )

    store.build_index(documents)
    print(f"Ingested {len(documents)} worlds.")


if __name__ == "__main__":
    ingest_titles()
