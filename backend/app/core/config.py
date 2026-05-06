"""Application configuration."""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "GeoIntel Platform"
    data_dir: Path = Path.home() / ".geointel"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    copernicus_username: str | None = None
    copernicus_password: str | None = None
    usgs_api_key: str | None = None
    gee_service_account_json: str | None = None
    corona_username: str | None = None
    corona_password: str | None = None

    def ensure_dirs(self) -> None:
        (self.data_dir / "aoi").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "jobs").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "results").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "rasters").mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
