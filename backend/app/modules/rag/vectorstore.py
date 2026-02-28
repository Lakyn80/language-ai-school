import os
import pickle
from threading import Lock
from typing import Any, List

_MODEL_CACHE: dict[str, Any] = {}
_MODEL_LOCK = Lock()


class VectorStore:
    def __init__(self, index_path: str, model_name: str):
        self.index_path = index_path
        self.model_name = model_name

        self._model = None
        self._index = None
        self._documents: list[dict[str, Any]] | None = None

    def _load_model(self):
        if self._model is not None:
            return

        with _MODEL_LOCK:
            cached = _MODEL_CACHE.get(self.model_name)
            if cached is None:
                from sentence_transformers import SentenceTransformer

                cached = SentenceTransformer(
                    self.model_name,
                    device="cpu",
                    cache_folder="/app/.cache",
                )
                _MODEL_CACHE[self.model_name] = cached

        self._model = cached

    def _load_index(self):
        if self._index is not None and self._documents is not None:
            return

        if not os.path.exists(self.index_path):
            raise RuntimeError("FAISS index not found. Run ingest first.")

        with open(self.index_path, "rb") as handle:
            data = pickle.load(handle)

        self._index = data["index"]
        self._documents = data["documents"]

    def preload(self) -> None:
        self._load_model()
        self._load_index()

    def build_index(self, documents: List[dict]):
        import faiss
        import numpy as np

        self._load_model()

        ordered_documents = sorted(
            documents,
            key=lambda item: str(item.get("id", "")),
        )

        unique_documents: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        seen_texts: set[str] = set()
        for item in ordered_documents:
            doc_id = str(item.get("id", "")).strip()
            text = str(item.get("text", "")).strip()
            if not doc_id or not text:
                continue
            if doc_id in seen_ids or text in seen_texts:
                continue

            seen_ids.add(doc_id)
            seen_texts.add(text)
            unique_documents.append(item)

        if not unique_documents:
            raise RuntimeError("No documents available for index build.")

        texts = [doc["text"] for doc in unique_documents]
        embeddings = self._model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=False,
        ).astype(np.float32)
        faiss.normalize_L2(embeddings)

        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings)

        with open(self.index_path, "wb") as handle:
            pickle.dump(
                {
                    "index": index,
                    "documents": unique_documents,
                },
                handle,
            )

        self._index = index
        self._documents = unique_documents

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        import faiss
        import numpy as np

        self._load_model()
        self._load_index()

        if self._documents is None or self._index is None:
            return []

        available = len(self._documents)
        if available == 0:
            return []

        limited_k = max(1, min(int(top_k), available))

        embedding = self._model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=False,
        ).astype(np.float32)
        faiss.normalize_L2(embedding)

        _, indices = self._index.search(embedding, limited_k)

        results: list[dict[str, Any]] = []
        for idx in indices[0]:
            if idx < 0:
                continue
            if idx >= len(self._documents):
                continue
            results.append(self._documents[idx])

        return results
