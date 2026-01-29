from app.modules.rag.vectorstore import VectorStore
from app.core.config import settings


def search_rag(query: str, k: int = 5):

    store = VectorStore(
        index_path=settings.rag_index_path,
        model_name=settings.rag_embedding_model
    )

    return store.search(query, top_k=k)
