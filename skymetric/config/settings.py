from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'skymetric.db'}"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    SCRAPER_MODE: str = "mock"
    LOG_LEVEL: str = "INFO"
    SERPAPI_KEY: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
