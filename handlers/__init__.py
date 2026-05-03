from aiogram import Router

from handlers.add_wallet import router as add_router
from handlers.list_wallets import router as list_router
from handlers.start import router as start_router
from handlers.utility import router as utility_router


def setup_routers() -> Router:
    root = Router()
    root.include_router(utility_router)
    root.include_router(start_router)
    root.include_router(add_router)
    root.include_router(list_router)
    return root
