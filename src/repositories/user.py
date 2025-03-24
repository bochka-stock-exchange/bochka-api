from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User
from src.repositories.base import SQLAlchemyRepository
from src.repositories.exceptions import EntityReadError


class UserRepository(SQLAlchemyRepository[User]):
    def __init__(self):
        """
        Initializes a new UserRepository instance using the User model.
        
        Calls the parent repository initializer with the User model to set up database 
        operations specific to user entities.
        """
        super().__init__(User)

    async def get_by_api_key(self, session: AsyncSession, api_key: str) -> Optional[User]:
        """
        Retrieve a user by API key asynchronously.
        
        This method queries the database for a User record whose API key matches the
        provided value. If a matching user is found, it is returned; otherwise, None is
        returned. An EntityReadError is raised if a database error occurs during the query.
        
        Args:
            api_key: The API key used to identify the user.
        
        Returns:
            The User instance corresponding to the given API key or None if no match is found.
        
        Raises:
            EntityReadError: If an error occurs while querying the database.
        """
        try:
            user = await session.scalar(select(User).where(User.api_key == api_key))
            return user
        except Exception as e:
            raise EntityReadError(
                self.__class__.__name__, self.model.__tablename__, "", str(e)
            ) from e
