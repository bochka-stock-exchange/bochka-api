"""
from src.db import DatabaseManager


class UnitOfWork:
    def __init__(self):
        self.db_manager = DatabaseManager()

    async def __aenter__(self):
        self.session_generator = self.db_manager.get_async_session()
        self.session = await self.session_generator.__anext__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_val:
                await self.session.rollback()
            else:
                await self.session.commit()
        finally:
            await self.session.close()
            await self.session_generator.aclose()

    async def rollback(self):
        await self.session.rollback()

    async def commit(self):
        await self.session.commit()
"""
