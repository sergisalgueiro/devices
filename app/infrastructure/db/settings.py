from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Reads DATABASE_URL from the environment (injected by docker-compose)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str


db_settings = DatabaseSettings()
