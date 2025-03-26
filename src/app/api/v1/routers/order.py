from fastapi import APIRouter
from pydantic import UUID4

router = APIRouter(prefix="/order", tags=["order"])


@router.post("/")
async def create_order():
    raise NotImplementedError()


@router.get("/")
async def get_orders():
    raise NotImplementedError()


@router.get("/{order_id}")
async def get_order(order_id: UUID4):
    raise NotImplementedError()


@router.delete("/{order_id}")
async def delete_order(order_id: UUID4):
    raise NotImplementedError()
