from fastapi import APIRouter, Depends

from src.app.api import dependencies

router = APIRouter(prefix="/balance", tags=["balance"])


@router.get("", dependencies=[Depends(dependencies.permissions.get_current_user)])
async def get_balance():
    raise NotImplementedError


@router.post("/deposit", dependencies=[Depends(dependencies.permissions.get_current_user)])
async def deposit():
    raise NotImplementedError


@router.post("/withdraw", dependencies=[Depends(dependencies.permissions.get_current_user)])
async def withdraw():
    raise NotImplementedError
