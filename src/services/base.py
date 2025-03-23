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
        self.repo = repo
        self.create_schema = create_schema
        self.read_schema = read_schema
        self.update_schema = update_schema

    async def create(self, session: AsyncSession, create_schema: TCreate) -> TRead:
        service_logger.info(f"Creating {self.create_schema.__name__} entity.")

        data = self.pre_create(create_schema.model_dump(exclude_unset=True))

        try:
            entity = await self.repo.create(session, data)

        except repo_exceptions.EntityCreateError as e:
            service_logger.error(f"Error creating {self.create_schema.__name__}: {str(e)}")
            raise service_exceptions.EntityCreateError(self.__class__.__name__, str(e)) from e

        service_logger.info(f"Successfully created {self.create_schema.__name__}.")
        return self.read_schema.model_validate(entity)

    # способ изменить данные перед созданием без изменения Create схемы,
    # например, для генерации каких-либо значений перед созданием
    def pre_create(self, data: dict) -> dict:
        return data

    async def create_many(
        self, session: AsyncSession, create_schemas: list[TCreate]
    ) -> list[TRead]:
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
