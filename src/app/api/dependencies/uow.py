from collections.abc import AsyncGenerator, Callable
from typing import Annotated

from fastapi import Depends

from src import core
from src.core.uow import UnitOfWork

settings = core.config.get_settings()


def get_uow_factory(
    *,
    use_postgres: bool = True,
) -> Callable[[], AsyncGenerator[UnitOfWork]]:
    async def _get_uow() -> AsyncGenerator[UnitOfWork]:
        async with UnitOfWork(use_postgres=use_postgres) as uow:
            yield uow

    return _get_uow


Postgres = Annotated[UnitOfWork, Depends(get_uow_factory(use_postgres=True))]
