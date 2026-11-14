import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from aiogram import Bot
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.bot import build_dispatcher
from app.config import Settings
from app.db import Database
from app.web.routes import router


def create_app(settings: Settings | None = None, bot=None, polling: bool = True) -> FastAPI:
    """Фабрика. В тестах можно передать свой bot и polling=False."""
    settings = settings or Settings.from_env()
    own_bot = bot is None
    bot = bot or Bot(settings.bot_token)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logging.basicConfig(level=logging.INFO)
        db = Database(settings.db_path)
        await db.connect()
        app.state.settings, app.state.db, app.state.bot = settings, db, bot

        task = None
        if polling:
            dp = build_dispatcher(db, settings)
            task = asyncio.create_task(dp.start_polling(bot, handle_signals=False))
        yield
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        if own_bot:
            await bot.session.close()
        await db.close()

    app = FastAPI(title="Receipts", lifespan=lifespan, docs_url=None, redoc_url=None)
    app.mount("/static", StaticFiles(directory=Path(__file__).parent / "web" / "static"), name="static")
    app.include_router(router)
    return app
