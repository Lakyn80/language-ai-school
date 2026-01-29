from app.modules.rag.vectorstore import VectorStore


def search_rag(query: str, k: int = 5):
    store = VectorStore()

    try:
        return store.search(query, k=k)
    except RuntimeError as e:
        return {
            "error": str(e),
            "hint": "Run RAG ingest first"
        }
