from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from uuid_v7.base import uuid7

import src.repositories.exceptions as repo_exceptions
import src.services.exceptions as service_exceptions
from src.repositories.user import UserRepository
from src.schemas.user import UserCreate, UserRead
from src.services.base import BaseService


class UserService(BaseService[UserCreate, UserRead, UserCreate]):
    def __init__(self):
        """Initialize the UserService with repository and schema configurations.
        
        Instantiates a UserRepository and configures the base service with the appropriate
        schemas for creating, reading, and updating user data. The update schema is set to be
        the same as the creation schema.
        """
        self.repo = UserRepository()
        super().__init__(
            self.repo,
            create_schema=UserCreate,
            read_schema=UserRead,
            update_schema=UserCreate,
        )

    def prepare_data(self, data: dict) -> dict:
        """
        Add an API key to the data dictionary.
        
        Generates a new API key by concatenating "key-" with a UUID version 7, then inserts it into
        the dictionary under the "api_key" key and returns the updated dictionary.
        
        Args:
            data: A dictionary containing user data.
        
        Returns:
            The updated dictionary with the generated API key.
        """
        data["api_key"] = "key-" + str(uuid7())
        return data

    async def get_by_api_key(self, session: AsyncSession, api_key: str) -> Optional[UserRead]:
        """
        Asynchronously retrieves and validates a user based on the API key.
        
        This method queries the repository for user data corresponding to the provided API key and validates the result using the read schema. If user retrieval fails due to an underlying EntityReadError, a service-level EntityReadError is raised with the original error message.
        
        Parameters:
            api_key: The API key used to identify the user.
        
        Returns:
            Optional[UserRead]: A validated user record if found, otherwise None.
        
        Raises:
            service_exceptions.EntityReadError: If an error occurs while fetching user data.
        """
        try:
            user_data = await self.repo.get_by_api_key(session, api_key)
        except repo_exceptions.EntityReadError as e:
            raise service_exceptions.EntityReadError(self.__class__.__name__, str(e)) from e

        return self.read_schema.model_validate(user_data)
