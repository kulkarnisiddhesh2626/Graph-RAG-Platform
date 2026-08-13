from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    data_dir: Path = Path("data")
    chroma_dir: Path = Path("data/chroma")
    graph_path: Path = Path("data/graph.json")
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    openai_api_key: str | None = None


settings = Settings()
