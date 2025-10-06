from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from src.core import db


class UnitOfWork:
    def __init__(
        self,
        *,
        use_postgres: bool = True,
    ):
        self._postgres_manager = db.get_postgres_manager() if use_postgres else None
        self._postgres_session = None  # type: ignore[valid-type]

    async def __aenter__(self):
        if self._postgres_manager:
            self._postgres_session: AsyncSession = await self._postgres_manager.get_session()
            await self._postgres_session.begin()

        return self

    async def __aexit__(self, exc_type=None, exc=None, tb=None):
        try:
            if self._postgres_session:
                if exc_type is not None:
                    await self._postgres_session.rollback()
                else:
                    await self._postgres_session.commit()
        finally:
            if self._postgres_session:
                await self._postgres_session.close()

    @property
    def postgres_session(self) -> AsyncSession:
        assert self._postgres_session is not None
        return self._postgres_session
