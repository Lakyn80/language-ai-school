from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Language AI School"
    api_prefix: str = "/api"

    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # ---------- RAG ----------
    rag_index_path: str = "app/modules/rag/index/titles.faiss"
    rag_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    class Config:
        env_file = ".env"


settings = Settings()
