from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import src.app.models as models
import src.core as core


class Users(core.repositories.sqlalchemy.BaseCRUD[models.User]):
    def __init__(self):
        super().__init__(models.User)

    async def get_by_api_key(self, session: AsyncSession, api_key: str) -> Optional[models.User]:
        try:
            user = await session.scalar(select(models.User).where(models.User.api_key == api_key))
            return user
        except Exception as e:
            raise core.repositories.exceptions.EntityReadError(
                self.__class__.__name__, self.model.__tablename__, "", str(e)
            ) from e
