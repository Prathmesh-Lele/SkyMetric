from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # repo root
SKYMETRIC_DIR = Path(__file__).resolve().parent.parent     # skymetric/


class Settings(BaseSettings):
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'skymetric.db'}"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    SCRAPER_MODE: str = "live"
    LOG_LEVEL: str = "INFO"
    SERPAPI_KEY: str = ""

    model_config = {
        "env_file": str(SKYMETRIC_DIR / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
