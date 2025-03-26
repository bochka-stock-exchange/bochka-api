from abc import ABC, abstractmethod
from typing import Generic, Optional, Sequence, TypeVar, Union

from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")


class Abstract(ABC, Generic[ModelType]):
    # def __init__(self, model: type[ModelType]):
    #     self.model = model

    @abstractmethod
    async def create(self, session: AsyncSession, data: dict) -> ModelType:
        raise NotImplementedError

    @abstractmethod
    async def create_many(self, session: AsyncSession, data_list: list[dict]) -> list[ModelType]:
        raise NotImplementedError

    @abstractmethod
    async def read_by_id(
        self, session: AsyncSession, entity_id: Union[int, str]
    ) -> Optional[ModelType]:
        raise NotImplementedError

    @abstractmethod
    async def read_all(
        self, session: AsyncSession, page: int = 1, limit: int = 10
    ) -> Sequence[ModelType]:
        raise NotImplementedError

    @abstractmethod
    async def update_by_id(
        self, session: AsyncSession, entity_id: Union[int, str], data: dict
    ) -> Optional[ModelType]:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_id(self, session: AsyncSession, entity_id: Union[int, str]) -> bool:
        raise NotImplementedError
