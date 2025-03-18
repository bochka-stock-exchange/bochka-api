from src.db import DatabaseManager


class UnitOfWork:
    def __init__(self):
        self.db_manager = DatabaseManager()

    async def __aenter__(self):
        """Asynchronous context manager entry point."""
        self.session_generator = self.db_manager.get_async_session()
        self.session = await self.session_generator.__anext__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Asynchronous context manager exit point."""
        try:
            if exc_val:
                await self.session.rollback()
            else:
                await self.session.commit()
        finally:
            await self.session.close()
            await self.session_generator.aclose()

    async def rollback(self):
        """Roll back the current session."""
        await self.session.rollback()

    async def commit(self):
        """Commit the current session."""
        await self.session.commit()
