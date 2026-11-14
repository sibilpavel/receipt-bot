from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.keyboards import receipts_list
from app.config import Settings
from app.db import Database

router = Router()


@router.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Здесь появятся чеки по вашим платежам.\n"
        "Последние пять: /receipts"
    )


@router.message(Command("receipts"))
async def receipts(message: Message, db: Database, settings: Settings):
    payments = await db.list_for_user(message.from_user.id, limit=5)
    if not payments:
        await message.answer("Платежей пока нет. Чек придёт сюда сразу после оплаты.")
        return
    await message.answer("Последние платежи:", reply_markup=receipts_list(settings, payments))
