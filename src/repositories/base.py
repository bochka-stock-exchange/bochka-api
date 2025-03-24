from typing import Generic, Optional, Sequence, TypeVar, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.logger import repository_logger
from src.models import Base
from src.repositories.exceptions import (
    EntityCreateError,
    EntityDeleteError,
    EntityReadError,
    EntityUpdateError,
)

ModelType = TypeVar("ModelType", bound=Base)


class SQLAlchemyRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType]):
        """
        Initialize the repository with the specified SQLAlchemy model.
        
        Args:
            model: A SQLAlchemy model class representing the entity for CRUD operations.
        """
        self.model = model

    async def create(self, session: AsyncSession, data: dict) -> ModelType:
        """
        Creates a new model instance in the database.
        
        Constructs a new instance using the provided data, adds it to the session,
        flushes pending changes, and refreshes the instance to obtain its updated state.
        Raises an EntityCreateError if any error occurs during creation.
        
        Args:
            data: A dictionary containing the attributes for creating the model instance.
        
        Returns:
            The newly created model instance.
        """
        repository_logger.info(f"Creating a new {self.model.__name__}: {data}")

        try:
            instance = self.model(**data)
            session.add(instance)
            await session.flush()
            await session.refresh(instance)
        except Exception as e:
            repository_logger.error(
                f"Error creating {self.model.__name__}: {data}, Error: {e}",
                exc_info=True,
            )
            raise EntityCreateError(
                self.__class__.__name__, self.model.__tablename__, str(e)
            ) from e

        repository_logger.info(f"Successfully created {self.model.__name__}: {instance}")
        return instance

    async def create_many(self, session: AsyncSession, data_list: list[dict]) -> list[ModelType]:
        """
        Creates multiple model entities asynchronously.
        
        Instantiates multiple model objects from the provided list of data dictionaries, adds all
        to the session, flushes the session, and refreshes each instance. An EntityCreateError is
        raised if any error occurs during these operations.
        
        Args:
            data_list: A list of dictionaries containing initialization data for each model instance.
        
        Returns:
            The list of newly created model instances.
        
        Raises:
            EntityCreateError: If an exception occurs during entity creation.
        """
        repository_logger.info(f"Creating multiple {self.model.__name__} entities")

        try:
            instances = [self.model(**data) for data in data_list]
            session.add_all(instances)
            await session.flush()
            for instance in instances:
                await session.refresh(instance)
        except Exception as e:
            repository_logger.error(
                f"Error creating multiple {self.model.__name__} entities: {e}",
                exc_info=True,
            )
            raise EntityCreateError(
                self.__class__.__name__, self.model.__tablename__, str(e)
            ) from e

        repository_logger.info(f"Successfully created multiple {self.model.__name__} entities")
        return instances

    async def read_by_id(
        self, session: AsyncSession, entity_id: Union[int, str]
    ) -> Optional[ModelType]:
        """
        Retrieve a model instance by its ID.
        
        This asynchronous function fetches an entity from the database using the provided identifier.
        It logs the retrieval process and, if an error occurs during the fetch, logs the error details before
        raising an EntityReadError. If no entity is found, a warning is logged and None is returned.
        
        Parameters:
            entity_id: The unique identifier of the entity to retrieve.
        
        Returns:
            The fetched model instance if found; otherwise, None.
        
        Raises:
            EntityReadError: If an error occurs while retrieving the entity.
        """
        repository_logger.info(f"Fetching {self.model.__name__} by ID: {entity_id}")

        try:
            entity = await session.get(self.model, entity_id)
        except Exception as e:
            repository_logger.error(
                f"Error fetching {self.model.__name__} with ID: {entity_id}, Error: {e}",
                exc_info=True,
            )
            raise EntityReadError(
                self.__class__.__name__,
                self.model.__tablename__,
                f"entity_id: {entity_id}",
                str(e),
            ) from e

        if entity:
            repository_logger.info(f"Found {self.model.__name__} with ID: {entity_id}")
        else:
            repository_logger.warning(f"No {self.model.__name__} found with ID: {entity_id}")

        return entity

    async def read_all(
        self, session: AsyncSession, page: int = 1, limit: int = 10
    ) -> Sequence[ModelType]:
        """
        Retrieves paginated model entities.
        
        This asynchronous method fetches a subset of model instances using the specified
        page and limit values to compute the query offset. If an error occurs during the
        database fetch, an EntityReadError is raised.
        """
        repository_logger.info(
            f"Fetching all {self.model.__name__} entities. Page: {page}, Limit: {limit}"
        )

        try:
            result = await session.scalars(
                select(self.model).offset((page - 1) * limit).limit(limit)
            )
            entities = result.all()
        except Exception as e:
            repository_logger.error(
                f"Error fetching all {self.model.__name__} entities, Error: {e}",
                exc_info=True,
            )
            raise EntityReadError(
                self.__class__.__name__, self.model.__tablename__, "", str(e)
            ) from e

        repository_logger.info(f"Fetched {len(entities)} {self.model.__name__} entities")
        return entities

    async def update_by_id(
        self, session: AsyncSession, entity_id: Union[int, str], data: dict
    ) -> Optional[ModelType]:
        """
        Update an entity by its ID with new values.
        
        Args:
            entity_id: The identifier of the entity to update.
            data: A dictionary of attribute-value pairs to update on the entity.
        
        Returns:
            The updated entity instance if found; otherwise, None.
        
        Raises:
            EntityUpdateError: If an error occurs during the update process.
        """
        repository_logger.info(f"Updating {self.model.__name__} with ID: {entity_id}, Data: {data}")

        try:
            instance = await self.read_by_id(session, entity_id)
            if instance:
                for key, value in data.items():
                    setattr(instance, key, value)
                await session.flush()
                await session.refresh(instance)
        except Exception as e:
            repository_logger.error(
                f"Error updating {self.model.__name__} with ID: {entity_id}, Error: {e}",
                exc_info=True,
            )
            raise EntityUpdateError(
                self.__class__.__name__,
                self.model.__tablename__,
                f"entity_id: {entity_id}",
                str(e),
            ) from e

        if instance:
            repository_logger.info(
                f"Successfully updated {self.model.__name__} with ID: {entity_id}"
            )
        else:
            repository_logger.warning(f"No {self.model.__name__} updated for ID: {entity_id}")
        return instance

    async def delete_by_id(self, session: AsyncSession, entity_id: Union[int, str]) -> bool:
        """
        Deletes an entity with the specified ID from the database.
        
        This method attempts to locate the entity by its ID. If found, it deletes the entity from
        the session and flushes the changes. It returns True if deletion is performed, or False if no
        entity with the given ID exists.
        
        Raises:
            EntityDeleteError: If an error occurs during the deletion process.
        """
        repository_logger.info(f"Deleting {self.model.__name__} with ID: {entity_id}")

        try:
            instance = await self.read_by_id(session, entity_id)
            if instance:
                await session.delete(instance)
                await session.flush()
                return True
            return False
        except Exception as e:
            repository_logger.error(
                f"Error deleting {self.model.__name__} with ID: {entity_id}, Error: {e}",
                exc_info=True,
            )
            raise EntityDeleteError(
                self.__class__.__name__,
                self.model.__tablename__,
                f"entity_id: {entity_id}",
                str(e),
            ) from e
