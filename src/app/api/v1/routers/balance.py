from fastapi import APIRouter

router = APIRouter(prefix="/balance", tags=["balance"])


@router.get("/")
async def get_balance():
    raise NotImplementedError


@router.post("/deposit")
async def deposit():
    raise NotImplementedError


@router.post("/deposit")
async def withdraw():
    raise NotImplementedError
