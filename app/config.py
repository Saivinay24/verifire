"""Runtime settings, read once from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://localhost/scammap"
    # Keyed hashing of reporter identity; must be set to a long random value in production.
    reporter_hmac_secret: str = "dev-only-secret-change-me"
    allowed_origin: str = "*"
    log_level: str = "INFO"
    # Key for the dispute reviewer's endpoints and page. Unset means reviewing is switched off.
    review_key: str = ""

    @property
    def sqlalchemy_url(self) -> str:
        """Render and most hosts hand out `postgres://` URLs; SQLAlchemy needs the psycopg driver named."""
        url = self.database_url
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url[len(prefix) :]
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
