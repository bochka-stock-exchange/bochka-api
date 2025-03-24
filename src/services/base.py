from typing import Generic, Optional, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

import src.repositories.exceptions as repo_exceptions
import src.services.exceptions as service_exceptions
from src.logger import service_logger
from src.repositories.base import SQLAlchemyRepository

TCreate = TypeVar("TCreate", bound=BaseModel)
TRead = TypeVar("TRead", bound=BaseModel)
TUpdate = TypeVar("TUpdate", bound=BaseModel)


class BaseService(Generic[TCreate, TRead, TUpdate]):
    def __init__(
        self,
        repo: SQLAlchemyRepository,
        create_schema: type[TCreate],
        read_schema: type[TRead],
        update_schema: type[TUpdate],
    ):
        """
        Initializes the BaseService with a repository and CRUD schemas.
        
        Sets up the service by assigning the SQLAlchemy repository instance and the Pydantic model classes for creating, reading, and updating entities.
        """
        self.repo = repo
        self.create_schema = create_schema
        self.read_schema = read_schema
        self.update_schema = update_schema

    async def create(self, session: AsyncSession, create_schema: TCreate) -> TRead:
        """
        Creates a new entity from the provided creation schema.
        
        Converts the creation schema to a dictionary (excluding unset fields) and uses it to
        create the entity via the repository. If creation fails, logs the error and raises a
        service-specific EntityCreateError. On success, validates and returns the created entity.
        """
        service_logger.info(f"Creating {self.create_schema.__name__} entity.")

        data = self.prepare_data(create_schema.model_dump(exclude_unset=True))

        try:
            entity = await self.repo.create(session, data)

        except repo_exceptions.EntityCreateError as e:
            service_logger.error(f"Error creating {self.create_schema.__name__}: {str(e)}")
            raise service_exceptions.EntityCreateError(self.__class__.__name__, str(e)) from e

        service_logger.info(f"Successfully created {self.create_schema.__name__}.")

        return self.read_schema.model_validate(entity)

    # способ изменить данные перед созданием без изменения Create схемы,
    # например, для генерации каких-либо значений перед созданием
    def prepare_data(self, data: dict) -> dict:
        """
        Prepares input data for entity creation.
        
        This hook method allows subclasses to modify or validate the input data before it is used
        in entity creation. By default, it returns the data unchanged.
        """
        return data

    async def create_many(
        self, session: AsyncSession, create_schemas: list[TCreate]
    ) -> list[TRead]:
        """
        Creates multiple entities from provided creation schemas.
        
        This method converts each creation schema into a dictionary (excluding unset values)
        and attempts to create entities in bulk via the repository. The resulting entities are
        validated against the read schema before being returned.
        
        Args:
            session: Asynchronous database session for executing queries.
            create_schemas: List of Pydantic models with the data for entity creation.
        
        Raises:
            EntityCreateError: If an error occurs during the creation of entities.
        
        Returns:
            A list of entities validated according to the read schema.
        """
        service_logger.info(f"Creating multiple {self.create_schema.__name__} entities.")

        data = [schema.model_dump(exclude_unset=True) for schema in create_schemas]

        try:
            entities = await self.repo.create_many(session, data)

        except repo_exceptions.EntityCreateError as e:
            service_logger.error(f"Error creating entities: {str(e)}")
            raise service_exceptions.EntityCreateError(self.__class__.__name__, str(e)) from e

        validated_entities: list[TRead] = [
            self.read_schema.model_validate(entity) for entity in entities
        ]

        service_logger.info(f"Successfully created {len(entities)} entities.")
        return validated_entities

    async def read_by_id(self, session: AsyncSession, entity_id: Union[int, str]) -> TRead:
        """
        Retrieve an entity by its unique identifier.
        
        Fetches the entity from the repository using the provided session and identifier,
        validates it with the configured read schema, and returns the validated model.
        If the repository read operation fails, an EntityReadError is raised.
        If no entity is found for the given ID, an EntityNotFoundError is raised.
        
        Raises:
            EntityReadError: If an error occurs during the read operation.
            EntityNotFoundError: If the entity does not exist.
        """
        service_logger.info(f"Reading {self.read_schema.__name__} with ID: {entity_id}")

        try:
            entity = await self.repo.read_by_id(session, entity_id)

        except repo_exceptions.EntityReadError as e:
            service_logger.error(
                f"Error reading {self.read_schema.__name__} with ID {entity_id}: {str(e)}"
            )
            raise service_exceptions.EntityReadError(self.__class__.__name__, str(e)) from e

        if not entity:
            service_logger.error(f"Entity with ID {entity_id} not found.")
            raise service_exceptions.EntityNotFoundError(
                self.__class__.__name__, f"entity_id: {entity_id}"
            )

        service_logger.info(
            f"Successfully fetched {self.update_schema.__name__} with ID {entity_id}"
        )
        return self.read_schema.model_validate(entity)

    async def read_all(self, session: AsyncSession, page: int = 1, limit: int = 10) -> list[TRead]:
        """
        Retrieves a paginated list of validated entities.
        
        Fetches entities from the repository using the provided session, page, and limit
        parameters, and validates each entity with the read schema. If an error occurs
        during retrieval, it logs the error and raises a service-specific EntityReadError.
        """
        service_logger.info(
            f"Reading all {self.read_schema.__name__} entities (Page: {page}, Limit: {limit})"
        )

        try:
            entities = await self.repo.read_all(session, page, limit)

        except repo_exceptions.EntityReadError as e:
            service_logger.error(f"Error reading all entities: {str(e)}")
            raise service_exceptions.EntityReadError(self.__class__.__name__, str(e)) from e

        validated_entities = [self.read_schema.model_validate(e) for e in entities]

        service_logger.info(f"Successfully fetched {len(entities)} entities.")
        return validated_entities

    async def update_by_id(
        self,
        session: AsyncSession,
        entity_id: Union[int, str],
        update_schema: TUpdate,
    ) -> Optional[TRead]:
        """
        Updates an entity by its ID.
        
        This asynchronous method applies only the provided update fields to the entity and returns the
        validated, updated entity. If no entity exists with the specified identifier, it raises an
        EntityNotFoundError. Repository errors during the update are caught and re-raised as
        EntityUpdateError exceptions.
        
        Args:
            entity_id: The unique identifier of the entity to update.
            update_schema: A Pydantic model containing the update fields; only set fields are applied.
        
        Returns:
            The updated entity as validated by the read schema.
        
        Raises:
            EntityNotFoundError: If the entity with the given identifier does not exist.
            EntityUpdateError: If an error occurs during the update operation.
        """
        service_logger.info(f"Updating {self.update_schema.__name__} with ID: {entity_id}")

        data = update_schema.model_dump(exclude_unset=True)

        try:
            updated_entity = await self.repo.update_by_id(session, entity_id, data)

            if not updated_entity:
                service_logger.error(f"Entity with ID {entity_id} not found for update.")
                raise service_exceptions.EntityNotFoundError(
                    self.__class__.__name__, f"entity_id: {entity_id}"
                )

        except repo_exceptions.EntityUpdateError as e:
            service_logger.error(f"Error updating entity with ID {entity_id}: {str(e)}")
            raise service_exceptions.EntityUpdateError(self.__class__.__name__, str(e)) from e

        service_logger.info(
            f"Successfully updated {self.update_schema.__name__} with ID {entity_id}."
        )
        return self.read_schema.model_validate(updated_entity)

    async def delete_by_id(self, session: AsyncSession, entity_id: Union[int, str]) -> bool:
        """
        Deletes an entity by its ID.
        
        Logs the deletion attempt, delegates deletion to the repository, and handles any errors.
        If the repository raises an error during deletion, the function logs the error and
        raises a service-specific deletion exception. If no entity is found with the provided ID,
        a not-found exception is raised.
        
        Returns:
            A boolean indicating whether the deletion was successful.
        
        Raises:
            service_exceptions.EntityDeleteError: If an error occurs during deletion.
            service_exceptions.EntityNotFoundError: If no entity exists with the specified ID.
        """
        service_logger.info(f"Deleting {self.read_schema.__name__} with ID: {entity_id}")

        try:
            is_deleted = await self.repo.delete_by_id(session, entity_id)

        except repo_exceptions.EntityDeleteError as e:
            service_logger.error(f"Error deleting entity with ID {entity_id}: {str(e)}")
            raise service_exceptions.EntityDeleteError(self.__class__.__name__, str(e)) from e

        if not is_deleted:
            service_logger.error(f"Entity with ID {entity_id} not found for deletion.")
            raise service_exceptions.EntityNotFoundError(
                self.__class__.__name__, f"entity_id: {entity_id}"
            )

        service_logger.info(f"Successfully deleted entity with ID {entity_id}.")
        return is_deleted
