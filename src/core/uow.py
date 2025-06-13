from sqlalchemy import text
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)
import asyncpg
from src.core.utils.decorators.retry import is_retryable_db_error
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential
from src.core import db, config, settings

settings = config.get_settings()


def is_serialization_error(exc: BaseException) -> bool:
    return isinstance(exc, (OperationalError, DBAPIError)) and isinstance(
        getattr(exc, "orig", None), asyncpg.exceptions.SerializationError
    )


class UnitOfWork:
    def __init__(self, *, use_postgres: bool = True, max_retries: int = 5):
        self._use_postgres = use_postgres
        self._max_retries = max_retries
        self._postgres_manager = db.get_postgres_manager() if use_postgres else None
        self._postgres_session = None

    async def __aenter__(self):
        if self._postgres_manager:
            self._postgres_session = await self._postgres_manager.get_session()
            await self._postgres_session.begin()
            await self._postgres_session.execute(text("SET lock_timeout = 10000"))
        return self

    async def __aexit__(self, exc_type=None, exc=None, tb=None):
        try:
            if self._postgres_session:
                if exc_type is not None:
                    await self._postgres_session.rollback()
                else:
                    try:
                        await self._postgres_session.commit()
                    except Exception as commit_ex:
                        await self._postgres_session.rollback()

                        # Пометка для повторной попытки
                        if is_serialization_error(commit_ex):
                            raise  # Будет перехвачено tenacity

                        raise
        finally:
            if self._postgres_session:
                await self._postgres_session.close()
            self._postgres_session = None

    @property
    def postgres_session(self) -> AsyncSession:
        if self._postgres_session is None:
            raise RuntimeError("Сессия PostgreSQL не инициализирована")
        return self._postgres_session
