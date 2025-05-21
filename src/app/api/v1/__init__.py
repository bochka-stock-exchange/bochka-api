from fastapi import APIRouter

from . import routers

router = APIRouter(prefix="/v1")
router.include_router(routers.public)
router.include_router(routers.balance)
router.include_router(routers.order)
router.include_router(routers.admin)
router.include_router(routers.debug)
