import logging

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
            self._postgres_session = await self._postgres_manager.get_session()
            await self._postgres_session.begin()
        return self

    async def __aexit__(self, exc_type=None, exc=None, tb=None):
        try:
            if self._postgres_session:
                if exc_type is not None:
                    try:
                        await self._postgres_session.rollback()
                    except Exception as rollback_ex:
                        logging.exception(f"Rollback failed: {rollback_ex}")
                    finally:
                        await self._reset_session()
                else:
                    try:
                        await self._postgres_session.commit()
                    except Exception:
                        await self._reset_session()
                        raise
        finally:
            if self._postgres_session:
                await self._postgres_session.close()
            self._postgres_session = None

    async def _reset_session(self):
        logging.debug("RESET SESSION CALLED")
        try:
            self._postgres_session.expunge_all()
            await self._postgres_session.rollback()

            await self._postgres_session.close()
            self._postgres_session = await self._postgres_manager.get_session()
            await self._postgres_session.begin()
        except Exception as reset_ex:
            logging.exception(f"Session reset failed: {reset_ex}")
            self._postgres_session = None

    @property
    def postgres_session(self) -> AsyncSession:
        assert self._postgres_session is not None
        return self._postgres_session
