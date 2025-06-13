from uuid import UUID

from src import core
from src.app import models, repositories, schemas, services

from . import exceptions


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

        self.instruments_service = services.Instruments()
        self.users_service = services.Users()

    async def transfer(
        self,
        uow: core.UnitOfWork,
        from_user_id: UUID,
        to_user_id: UUID,
        instrument_id: UUID,
        amount: int,
    ) -> None:
        from_balance = await self.get_or_create_user_balance(uow, from_user_id, instrument_id)

        to_balance = await self.get_or_create_user_balance(uow, to_user_id, instrument_id)

        from_balance.amount -= amount
        to_balance.amount += amount

        await self.update_by_id(
            uow,
            {"user_id": from_user_id, "instrument_id": instrument_id},
            schemas.balance.Update(amount=from_balance.amount),
        )
        await self.update_by_id(
            uow,
            {"user_id": to_user_id, "instrument_id": instrument_id},
            schemas.balance.Update(amount=to_balance.amount),
        )

    async def get_or_create_user_balance(
        self, uow: core.UnitOfWork, user_id: UUID, instrument_id: UUID
    ) -> schemas.balance.Read:
        try:
            balance = await self.read_by_id(
                uow, {"user_id": user_id, "instrument_id": instrument_id}
            )
        except core.services.exceptions.EntityNotFoundError:
            balance = await self.create(
                uow,
                schemas.balance.Create(
                    user_id=user_id,
                    instrument_id=instrument_id,
                    amount=0,
                ),
            )

        return balance

    async def deposit(
        self, uow: core.UnitOfWork, operation_data: schemas.balance.Operation
    ) -> None:
        await self.users_service.read_by_id(uow, operation_data.user_id)
        instrument = await self.instruments_service.read_by_ticker(uow, operation_data.ticker)
        balance = await self.get_or_create_user_balance(uow, operation_data.user_id, instrument.id)

        balance.amount += operation_data.amount
        await self.update_by_id(
            uow,
            {"user_id": operation_data.user_id, "instrument_id": instrument.id},
            schemas.balance.Update(amount=balance.amount),
        )

    async def withdraw(
        self, uow: core.UnitOfWork, operation_data: schemas.balance.Operation
    ) -> None:
        await self.users_service.read_by_id(uow, operation_data.user_id)
        instrument = await self.instruments_service.read_by_ticker(uow, operation_data.ticker)

        try:
            balance = await self.read_by_id(
                uow, {"user_id": operation_data.user_id, "instrument_id": instrument.id}
            )

            if balance.available_amount < operation_data.amount:
                raise exceptions.InsufficientBalanceError(
                    operation_data.user_id, instrument.ticker
                )

        except core.services.exceptions.EntityNotFoundError as e:
            raise exceptions.InsufficientBalanceError(
                operation_data.user_id, instrument.ticker
            ) from e

        else:
            balance.amount -= operation_data.amount
            await self.update_by_id(
                uow,
                {"user_id": operation_data.user_id, "instrument_id": instrument.id},
                schemas.balance.Update(amount=balance.amount),
            )
