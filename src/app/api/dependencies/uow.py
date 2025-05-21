from collections.abc import AsyncGenerator, Callable
from typing import Annotated

from fastapi import Depends

from src import core

settings = core.config.get_settings()


def get_uow_factory(
    *,
    use_postgres: bool = True,
) -> Callable[[], AsyncGenerator[core.UnitOfWork]]:
    async def _get_uow() -> AsyncGenerator[core.UnitOfWork]:
        async with core.UnitOfWork(use_postgres=use_postgres) as uow:
            yield uow

    return _get_uow


Postgres = Annotated[core.UnitOfWork, Depends(get_uow_factory(use_postgres=True))]
