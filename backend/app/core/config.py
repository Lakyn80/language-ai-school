from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Language AI School"
    api_prefix: str = "/api"

    # ---------- LLM ----------
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # ---------- RAG ----------
    rag_index_path: str = "app/modules/rag/index/titles.faiss"
    rag_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # ---------- POSTGRES ----------
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "language_ai_school"
    postgres_user: str = "language_ai"
    postgres_password: str = "language_ai_pass"

    class Config:
        env_file = ".env"


settings = Settings()
