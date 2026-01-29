from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Language AI School"
    api_prefix: str = "/api"

    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    class Config:
        env_file = ".env"


settings = Settings()
