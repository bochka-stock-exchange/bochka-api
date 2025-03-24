from pathlib import Path

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.utils.singleton import SingletonDecorator


@SingletonDecorator
class Settings(BaseSettings):
    APP_TITLE: str = "Bochka stock exchange"
    APP_DESCRIPTION: str = "API for Bochka stock exchange"
    APP_VERSION: str = "0.1.0"

    DEBUG: bool = False

    CSRF_COOKIE_NAME: str = "csrftoken"
    CSRF_EXPIRE_TIME: int = 86400 * 7  # 7 дней

    DOMAIN: str = "example.site"

    ALLOW_ORIGINS: list[str] = ["*"]
    ALLOW_HOSTS: list[str] = ["*"]

    POSTGRES_HOST: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "postgres"

    API_PREFIX: str = "/api"

    TOKEN_PREFIX: str = "TOKEN"

    MAX_IMAGE_SIZE: int = 1024 * 1024 * 10  # 10 MB

    @property
    def DATABASE_URL(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    model_config = SettingsConfigDict(env_file=Path(__file__).parents[1] / ".env", extra="ignore")


def get_settings():
    return Settings.get_instance()
