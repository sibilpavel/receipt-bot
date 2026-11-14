from aiogram import Dispatcher

from app.bot.handlers import router
from app.config import Settings
from app.db import Database


def build_dispatcher(db: Database, settings: Settings) -> Dispatcher:
    dp = Dispatcher(db=db, settings=settings)  # попадут в аргументы хендлеров
    dp.include_router(router)
    return dp
