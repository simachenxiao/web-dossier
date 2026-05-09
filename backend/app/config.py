from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Dossier V5 Backend"
    database_url: str = "sqlite:///./dossier_v5.db"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="DOSSIER_")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]
