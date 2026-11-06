from __future__ import annotations

import threading
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select

from src import core
from src.app import models, repositories, schemas, services

if TYPE_CHECKING:
    from src.core.uow import UnitOfWork


class Balances(
    core.services.BaseCRUD[
        schemas.balance.Create,
        schemas.balance.Read,
        schemas.balance.Update,
        schemas.balance.Filters,
        schemas.balance.SortParams,
        models.Balance,
    ],
):
    def __init__(self):
        self.repo = repositories.Balances()
        super().__init__(
            repo=self.repo,
            create_schema=schemas.balance.Create,
            read_schema=schemas.balance.Read,
            update_schema=schemas.balance.Update,
            filters_schema=schemas.balance.Filters,
        )

    async def read_by_composite_id(
        self,
        uow: UnitOfWork,
        user_id: UUID,
        instrument_id: UUID,
        *,
        include_deleted: bool = False,
    ) -> schemas.balance.Read:
        balances = await self.read_many(
            uow,
            filters=schemas.instruments.Filters(user_id=user_id, instrument_id=instrument_id),
            include_deleted=include_deleted,
        )

        if not balances:
            raise core.services.exceptions.EntityNotFoundError(
                self.__class__.__name__,
                f"user_id: {user_id}, instrument_id {instrument_id}",
            )

        return balances[0]

    async def read_by_id(
        self,
        uow: UnitOfWork,
        balance_id: core.custom_types.EntityID,
        *,
        include_deleted: bool = False,
    ) -> schemas.balance.Read:
        if isinstance(balance_id, dict):
            return await self.read_by_composite_id(
                uow,
                user_id=balance_id["user_id"],  # type: ignore[valid-type]
                instrument_id=balance_id["instrument_id"],  # type: ignore[valid-type]
            )

        return await super().read_by_id(uow, balance_id, include_deleted=include_deleted)

    async def update_by_id(
        self,
        uow: UnitOfWork,
        balance_id: core.custom_types.EntityID,
        update_schema: schemas.balance.Update,
    ) -> schemas.balance.Read:
        if isinstance(balance_id, dict):
            balance = await self.read_by_composite_id(
                uow,
                user_id=balance_id["user_id"],  # type: ignore[valid-type]
                instrument_id=balance_id["instrument_id"],  # type: ignore[valid-type]
            )
            balance_id = balance.id

        return await super().update_by_id(uow, balance_id, update_schema)

    async def delete_by_id(self, uow: UnitOfWork, balance_id: core.custom_types.EntityID) -> bool:
        if isinstance(balance_id, dict):
            balance = await self.read_by_composite_id(
                uow,
                user_id=balance_id["user_id"],  # type: ignore[valid-type]
                instrument_id=balance_id["instrument_id"],  # type: ignore[valid-type]
            )
            balance_id = balance.id

        return await super().delete_by_id(uow, balance_id)

    async def transfer(
        self,
        uow: UnitOfWork,
        from_user_id: UUID,
        to_user_id: UUID,
        instrument_id: UUID,
        amount: int,
    ) -> None:
        session = uow.postgres_session
        async with session.begin_nested():
            from_balance_query = (
                select(self.repo.model)
                .where(
                    self.repo.model.user_id == from_user_id,
                    self.repo.model.instrument_id == instrument_id,
                )
                .with_for_update()
            )
            from_balance = await session.scalar(from_balance_query)
            if from_balance is None:
                from_balance = await self.create(
                    uow,
                    schemas.balance.Create(
                        user_id=from_user_id,
                        instrument_id=instrument_id,
                        amount=0,
                    ),
                )

            if from_balance.amount < amount:
                instrument = await services.Instruments().read_by_id(uow, instrument_id)
                raise services.exceptions.InsufficientBalanceError(from_user_id, instrument.ticker)

            to_balance_query = (
                select(self.repo.model)
                .where(
                    self.repo.model.user_id == to_user_id,
                    self.repo.model.instrument_id == instrument_id,
                )
                .with_for_update()
            )
            to_balance = await uow.postgres_session.scalar(to_balance_query)
            if to_balance is None:
                to_balance = await self.create(
                    uow,
                    schemas.balance.Create(
                        user_id=to_user_id,
                        instrument_id=instrument_id,
                        amount=0,
                    ),
                )

            from_balance.amount -= amount
            to_balance.amount += amount

            await session.flush()

    async def get_or_create_user_balance(
        self,
        uow: UnitOfWork,
        user_id: UUID,
        instrument_id: UUID,
    ) -> schemas.balance.Read:
        await services.Users().read_by_id(uow, user_id)
        await services.Instruments().read_by_id(uow, instrument_id)
        try:
            async with uow.postgres_session.begin_nested():
                with threading.Lock():
                    balance = await self.read_by_id(
                        uow,
                        {"user_id": user_id, "instrument_id": instrument_id},
                    )
        except core.services.exceptions.EntityNotFoundError:
            async with uow.postgres_session.begin_nested():
                with threading.Lock():
                    balance = await self.create(
                        uow,
                        schemas.balance.Create(
                            user_id=user_id,
                            instrument_id=instrument_id,
                            amount=0,
                        ),
                    )

        return balance
