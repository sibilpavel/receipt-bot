import re
import time

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.keyboards import open_receipt, receipts_list
from app.config import FARE_KOP, Settings
from app.db import Database, Payment

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


# Тестовый режим: "5 12345" -> автобус №5, номер платежа 12345.
# Первое число — номер автобуса, второе — номер платежа (буквы/цифры/_/-).
# Цена проезда всегда одна и та же.
TEST_INPUT = re.compile(r"^\s*(\d{1,4})\s+([A-Za-z0-9_\-]{1,64})\s*$")


def parse_test_input(text: str) -> tuple[str, str] | None:
    """Возвращает (номер_автобуса, номер_платежа) или None."""
    m = TEST_INPUT.match(text or "")
    if not m:
        return None
    return m.group(1), m.group(2)


@router.message(F.text.regexp(TEST_INPUT))
async def test_payment(message: Message, db: Database, settings: Settings):
    if not settings.test_mode:
        return
    parsed = parse_test_input(message.text)
    if not parsed:
        return
    bus, payment_id = parsed
    # Повторный ввод своего номера обновляет автобус и сумму (всегда 53 ₽).
    await db.upsert_payment(Payment(payment_id, message.from_user.id, FARE_KOP,
                                 f"Автобус: №{bus}", int(time.time())))
    p = await db.get_payment(payment_id)
    if p.tg_user_id != message.from_user.id:
        await message.answer("Этот номер платежа уже занят другим пользователем.")
        return
    await message.answer(
        f"Оплата автобуса номер {bus} прошла",
        reply_markup=open_receipt(settings, p.id),
    )
