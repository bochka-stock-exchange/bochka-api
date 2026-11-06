from fastapi import APIRouter

from src.app import schemas
from src.app.api import dependencies

router = APIRouter(prefix="/debug", tags=["debug"])


@router.post("/healthcheck")
async def healthcheck():
    return 1


@router.get("/profile", response_model=schemas.users.Read)
async def get_profile(
    current_user: dependencies.permissions.CurrentUser,
):
    return current_user


@router.get("/profile-admin", response_model=schemas.users.Read)
async def get_profile_admin(
    current_user: dependencies.permissions.AdminUser,
):
    return current_user


@router.get("/users-all")
async def get_all_users(
    service: dependencies.services.Users,
    uow: dependencies.uow.Postgres,
) -> list[schemas.users.Read]:
    return await service.read_many(uow)
