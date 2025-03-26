from pathlib import Path

from pydantic import MongoDsn, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

import src.utils as utils


class PostgreSQLSettings(BaseSettings):
    POSTGRES_HOST: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "postgres"

    @property
    def DSN(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    @property
    def URL(self) -> str:
        return str(self.DSN)


class MongoDBSettings(BaseSettings):
    MONGO_HOST: str = "localhost"
    MONGO_USER: str = "mongo"
    MONGO_PORT: int = 27017
    MONGO_PASSWORD: str = "mongo"
    MONGO_DB: str = "admin"

    @property
    def DSN(self) -> MongoDsn:
        return MongoDsn.build(
            scheme="mongodb",
            username=self.MONGO_USER,
            password=self.MONGO_PASSWORD,
            host=self.MONGO_HOST,
            port=self.MONGO_PORT,
            path=self.MONGO_DB,
        )

    @property
    def URL(self) -> str:
        return str(self.DSN)


@utils.SingletonDecorator
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

    POSTGRES: PostgreSQLSettings = PostgreSQLSettings()
    # MONGO: MongoDBSettings = MongoDBSettings()

    API_PREFIX: str = "/api"

    TOKEN_PREFIX: str = "TOKEN"
    USER_ROLE: str = "USER"
    ADMIN_ROLE: str = "ADMIN"

    model_config = SettingsConfigDict(env_file=Path(__file__).parents[1] / ".env", extra="ignore")


def get_settings():
    return Settings()
