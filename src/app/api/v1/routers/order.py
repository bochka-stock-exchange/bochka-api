from fastapi import APIRouter, Depends
from pydantic import UUID4

from src.app.api import dependencies

router = APIRouter(prefix="/order", tags=["order"])


@router.post("", dependencies=[Depends(dependencies.permissions.get_current_user)])
async def create_order():
    raise NotImplementedError


@router.get("", dependencies=[Depends(dependencies.permissions.get_current_user)])
async def get_orders():
    raise NotImplementedError


@router.get("/{order_id}", dependencies=[Depends(dependencies.permissions.get_current_user)])
async def get_order(order_id: UUID4):
    raise NotImplementedError


@router.delete("/{order_id}", dependencies=[Depends(dependencies.permissions.get_current_user)])
async def delete_order(order_id: UUID4):
    raise NotImplementedError
