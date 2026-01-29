import os
import pickle
from typing import List


class VectorStore:
    def __init__(self, index_path: str, model_name: str):
        self.index_path = index_path
        self.model_name = model_name

        self._model = None
        self._index = None
        self._documents = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            # ⬇⬇⬇
            # lokální load – žádný HF request
            self._model = SentenceTransformer(
                self.model_name,
                device="cpu",
                cache_folder="/app/.cache"
            )

    def _load_index(self):
        if self._index is not None:
            return

        if not os.path.exists(self.index_path):
            raise RuntimeError("FAISS index not found. Run ingest first.")

        with open(self.index_path, "rb") as f:
            data = pickle.load(f)

        self._index = data["index"]
        self._documents = data["documents"]

    def build_index(self, documents: List[dict]):
        from sentence_transformers import SentenceTransformer
        import faiss

        model = SentenceTransformer(
            self.model_name,
            device="cpu",
            cache_folder="/app/.cache"
        )

        texts = [doc["text"] for doc in documents]
        embeddings = model.encode(texts)

        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)

        with open(self.index_path, "wb") as f:
            pickle.dump(
                {
                    "index": index,
                    "documents": documents,
                },
                f,
            )

    def search(self, query: str, top_k: int = 5) -> List[str]:
        self._load_index()
        self._load_model()

        embedding = self._model.encode([query])
        distances, indices = self._index.search(embedding, top_k)

        results = []
        for idx in indices[0]:
            results.append(self._documents[idx])

        return results
